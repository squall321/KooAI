"""
Multi-tier 캐시

L1 (로컬 인메모리 LRU) + L2 (Redis) 2단계 캐싱 전략.
"""

from typing import Any, Dict, List, Optional

import structlog

from .lru_cache import LRUCache
from .redis_cache import RedisCache

logger = structlog.get_logger(__name__)


class MultiTierCache:
    """
    2단계 캐시 시스템

    L1: 로컬 인메모리 LRU 캐시 (빠름, 작은 용량)
    L2: Redis 캐시 (중간 속도, 큰 용량, 공유)

    캐시 전략:
    1. GET: L1 → L2 → 데이터 소스
    2. SET: L1 + L2 동시 저장
    3. L1 miss + L2 hit → L1에 프로모션

    사용 예:
        cache = MultiTierCache(
            l1_max_size=1000,
            l2_cache=redis_cache
        )
        cache.set("key", "value")
        value = cache.get("key")  # L1에서 즉시 반환
    """

    def __init__(
        self,
        l2_cache: RedisCache,
        l1_max_size: int = 1000,
        l1_default_ttl: int = 300,
        promote_to_l1: bool = True,
    ):
        """
        Args:
            l2_cache: L2 Redis 캐시 인스턴스
            l1_max_size: L1 캐시 최대 크기
            l1_default_ttl: L1 기본 TTL (초)
            promote_to_l1: L2 hit 시 L1으로 프로모션 여부
        """
        self.l1 = LRUCache(max_size=l1_max_size, default_ttl=l1_default_ttl)
        self.l2 = l2_cache
        self.promote_to_l1 = promote_to_l1

        # 통계
        self._l1_hits = 0
        self._l2_hits = 0
        self._total_misses = 0
        self._promotions = 0

    def get(self, key: str, prefix: Optional[str] = None) -> Optional[Any]:
        """
        캐시에서 값 가져오기 (L1 → L2)

        Args:
            key: 캐시 키
            prefix: L2 키 prefix (선택적)

        Returns:
            캐시된 값 또는 None
        """
        # L1에서 먼저 확인
        full_key = self._make_full_key(key, prefix)
        value = self.l1.get(full_key)

        if value is not None:
            self._l1_hits += 1
            logger.debug("l1_cache_hit", key=key, prefix=prefix)
            return value

        # L1 miss, L2에서 확인
        value = self.l2.get(key, prefix=prefix)

        if value is not None:
            self._l2_hits += 1
            logger.debug("l2_cache_hit", key=key, prefix=prefix)

            # L2 hit → L1으로 프로모션
            if self.promote_to_l1:
                self.l1.set(full_key, value)
                self._promotions += 1

            return value

        # L1, L2 모두 miss
        self._total_misses += 1
        logger.debug("cache_miss_all_tiers", key=key, prefix=prefix)
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        prefix: Optional[str] = None,
        l1_only: bool = False,
    ) -> bool:
        """
        캐시에 값 저장 (L1 + L2)

        Args:
            key: 캐시 키
            value: 값
            ttl: Time to live (초)
            prefix: L2 키 prefix
            l1_only: L1에만 저장 (L2 스킵)

        Returns:
            저장 성공 여부
        """
        full_key = self._make_full_key(key, prefix)

        # L1에 저장
        self.l1.set(full_key, value, ttl=ttl)

        # L2에 저장 (l1_only가 아닌 경우)
        if not l1_only:
            success = self.l2.set(key, value, ttl=ttl, prefix=prefix)
            return success

        return True

    def delete(self, key: str, prefix: Optional[str] = None) -> bool:
        """
        캐시에서 키 삭제 (L1 + L2)

        Args:
            key: 캐시 키
            prefix: L2 키 prefix

        Returns:
            삭제 여부
        """
        full_key = self._make_full_key(key, prefix)

        # L1에서 삭제
        l1_deleted = self.l1.delete(full_key)

        # L2에서 삭제
        l2_deleted = self.l2.delete(key, prefix=prefix)

        return l1_deleted or l2_deleted

    def exists(self, key: str, prefix: Optional[str] = None) -> bool:
        """
        키 존재 여부 확인 (L1 → L2)

        Args:
            key: 캐시 키
            prefix: L2 키 prefix

        Returns:
            존재 여부
        """
        full_key = self._make_full_key(key, prefix)

        # L1에서 확인
        if self.l1.exists(full_key):
            return True

        # L2에서 확인
        return self.l2.exists(key, prefix=prefix)

    def get_many(self, keys: List[str], prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        여러 키 가져오기

        Args:
            keys: 키 리스트
            prefix: L2 키 prefix

        Returns:
            키-값 딕셔너리
        """
        result = {}
        l2_keys = []

        # L1에서 먼저 확인
        for key in keys:
            full_key = self._make_full_key(key, prefix)
            value = self.l1.get(full_key)

            if value is not None:
                result[key] = value
                self._l1_hits += 1
            else:
                l2_keys.append(key)

        # L1 miss인 키들을 L2에서 확인
        if l2_keys:
            l2_results = self.l2.get_many(l2_keys, prefix=prefix)

            for key, value in l2_results.items():
                result[key] = value
                self._l2_hits += 1

                # L1으로 프로모션
                if self.promote_to_l1:
                    full_key = self._make_full_key(key, prefix)
                    self.l1.set(full_key, value)
                    self._promotions += 1

            # 완전히 miss인 키 수
            self._total_misses += len(keys) - len(result)

        return result

    def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        prefix: Optional[str] = None,
    ) -> int:
        """
        여러 키-값 저장

        Args:
            mapping: 키-값 딕셔너리
            ttl: Time to live (초)
            prefix: L2 키 prefix

        Returns:
            저장된 키 수
        """
        # L1에 저장
        for key, value in mapping.items():
            full_key = self._make_full_key(key, prefix)
            self.l1.set(full_key, value, ttl=ttl)

        # L2에 저장
        return self.l2.set_many(mapping, ttl=ttl, prefix=prefix)

    def clear_l1(self) -> int:
        """
        L1 캐시만 클리어

        Returns:
            삭제된 엔트리 수
        """
        return self.l1.clear()

    def clear_prefix(self, prefix: str) -> int:
        """
        특정 prefix 클리어 (L2만)

        L1은 prefix를 구분하지 않으므로 전체 클리어가 필요한 경우
        clear_l1()을 별도로 호출해야 합니다.

        Args:
            prefix: 클리어할 prefix

        Returns:
            L2에서 삭제된 키 수
        """
        return self.l2.clear_prefix(prefix)

    def cleanup_expired(self) -> int:
        """
        L1에서 만료된 엔트리 정리

        Returns:
            정리된 엔트리 수
        """
        return self.l1.cleanup_expired()

    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 반환

        Returns:
            통계 딕셔너리
        """
        l1_stats = self.l1.get_stats()

        total_requests = self._l1_hits + self._l2_hits + self._total_misses
        overall_hit_rate = (
            (self._l1_hits + self._l2_hits) / total_requests if total_requests > 0 else 0.0
        )

        return {
            "l1": l1_stats,
            "l2": {
                "hits": self._l2_hits,
                "available": self.l2.ping(),
            },
            "overall": {
                "l1_hits": self._l1_hits,
                "l2_hits": self._l2_hits,
                "total_misses": self._total_misses,
                "hit_rate": overall_hit_rate,
                "promotions": self._promotions,
            },
        }

    def reset_stats(self) -> None:
        """통계 초기화"""
        self.l1.reset_stats()
        self._l1_hits = 0
        self._l2_hits = 0
        self._total_misses = 0
        self._promotions = 0

    def _make_full_key(self, key: str, prefix: Optional[str]) -> str:
        """L1용 전체 키 생성 (prefix 포함)"""
        if prefix:
            return f"{prefix}:{key}"
        return key


# Singleton instance
_multi_tier_cache_instance: Optional[MultiTierCache] = None


def get_multi_tier_cache() -> MultiTierCache:
    """Multi-tier 캐시 싱글톤 반환"""
    global _multi_tier_cache_instance

    if _multi_tier_cache_instance is None:
        from .redis_cache import get_cache

        redis_cache = get_cache()
        _multi_tier_cache_instance = MultiTierCache(l2_cache=redis_cache)

    return _multi_tier_cache_instance


def reset_multi_tier_cache() -> None:
    """싱글톤 초기화 (테스트용)"""
    global _multi_tier_cache_instance
    _multi_tier_cache_instance = None
