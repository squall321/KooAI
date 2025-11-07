"""
로컬 인메모리 LRU 캐시

빠른 접근을 위한 L1 캐시 구현.
"""

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CacheEntry:
    """캐시 엔트리"""

    value: Any
    expires_at: float
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_access: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        return time.time() > self.expires_at

    def access(self) -> None:
        """접근 기록"""
        self.access_count += 1
        self.last_access = time.time()


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) 캐시

    주요 기능:
    - LRU eviction policy
    - TTL 지원
    - Thread-safe operations
    - 메모리 제한
    - 통계 수집

    사용 예:
        cache = LRUCache(max_size=1000, default_ttl=300)
        cache.set("key", "value", ttl=60)
        value = cache.get("key")
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Args:
            max_size: 최대 엔트리 수
            default_ttl: 기본 TTL (초)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # 통계
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 가져오기

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # 만료 확인
            if entry.is_expired():
                del self._cache[key]
                self._expirations += 1
                self._misses += 1
                return None

            # LRU 업데이트 (맨 뒤로 이동)
            self._cache.move_to_end(key)
            entry.access()

            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        캐시에 값 저장

        Args:
            key: 캐시 키
            value: 값
            ttl: Time to live (초), None이면 default_ttl 사용
        """
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl

            expires_at = time.time() + ttl

            # 기존 키 업데이트
            if key in self._cache:
                self._cache[key] = CacheEntry(value, expires_at)
                self._cache.move_to_end(key)
                return

            # 새 키 추가
            # 크기 제한 확인
            if len(self._cache) >= self.max_size:
                # LRU 삭제 (가장 오래된 항목)
                self._cache.popitem(last=False)
                self._evictions += 1

            self._cache[key] = CacheEntry(value, expires_at)

    def delete(self, key: str) -> bool:
        """
        캐시에서 키 삭제

        Args:
            key: 캐시 키

        Returns:
            삭제 여부
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """
        모든 캐시 삭제

        Returns:
            삭제된 엔트리 수
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def exists(self, key: str) -> bool:
        """
        키 존재 여부 확인

        Args:
            key: 캐시 키

        Returns:
            존재 여부
        """
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._expirations += 1
                return False

            return True

    def cleanup_expired(self) -> int:
        """
        만료된 엔트리 정리

        Returns:
            정리된 엔트리 수
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]

            self._expirations += len(expired_keys)
            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 반환

        Returns:
            통계 딕셔너리
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "expirations": self._expirations,
            }

    def reset_stats(self) -> None:
        """통계 초기화"""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0

    def __len__(self) -> int:
        """캐시 크기 반환"""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """in 연산자 지원"""
        return self.exists(key)
