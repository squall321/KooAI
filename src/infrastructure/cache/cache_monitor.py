"""
캐시 모니터링 및 메트릭 수집

캐시 성능을 추적하고 최적화를 위한 인사이트 제공.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CacheMetric:
    """캐시 메트릭 데이터"""

    timestamp: float
    operation: str  # get, set, delete, etc.
    key: str
    hit: Optional[bool]  # get 작업에만 해당
    duration_ms: float  # 작업 소요 시간 (밀리초)
    tier: Optional[str] = None  # l1, l2, miss


@dataclass
class CacheStats:
    """캐시 통계 스냅샷"""

    timestamp: float = field(default_factory=time.time)
    total_requests: int = 0
    hits: int = 0
    misses: int = 0
    hit_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    errors: int = 0


class CacheMonitor:
    """
    캐시 모니터링 시스템

    주요 기능:
    - 실시간 메트릭 수집
    - 히트율 추적
    - 응답 시간 분석
    - 핫 키 감지
    - 통계 리포트 생성

    사용 예:
        monitor = CacheMonitor(window_size=1000)

        # 작업 기록
        monitor.record_get("user:123", hit=True, duration_ms=0.5, tier="l1")
        monitor.record_set("user:123", duration_ms=1.2)

        # 통계 조회
        stats = monitor.get_stats()
        print(f"Hit rate: {stats.hit_rate:.1%}")
    """

    def __init__(self, window_size: int = 10000, hot_key_threshold: int = 100):
        """
        Args:
            window_size: 메트릭 윈도우 크기 (최근 N개 작업만 보관)
            hot_key_threshold: 핫 키 판정 기준 (접근 횟수)
        """
        self.window_size = window_size
        self.hot_key_threshold = hot_key_threshold

        # 메트릭 큐 (고정 크기)
        self._metrics: Deque[CacheMetric] = deque(maxlen=window_size)

        # 키 접근 카운터
        self._key_access_counts: Dict[str, int] = {}

        # 에러 카운터
        self._errors = 0

    def record_get(
        self,
        key: str,
        hit: bool,
        duration_ms: float,
        tier: Optional[str] = None,
    ) -> None:
        """
        GET 작업 기록

        Args:
            key: 캐시 키
            hit: 히트 여부
            duration_ms: 소요 시간 (밀리초)
            tier: 히트된 계층 (l1, l2, 또는 None for miss)
        """
        metric = CacheMetric(
            timestamp=time.time(),
            operation="get",
            key=key,
            hit=hit,
            duration_ms=duration_ms,
            tier=tier if hit else "miss",
        )

        self._metrics.append(metric)
        self._increment_key_access(key)

    def record_set(self, key: str, duration_ms: float) -> None:
        """
        SET 작업 기록

        Args:
            key: 캐시 키
            duration_ms: 소요 시간 (밀리초)
        """
        metric = CacheMetric(
            timestamp=time.time(),
            operation="set",
            key=key,
            hit=None,
            duration_ms=duration_ms,
        )

        self._metrics.append(metric)

    def record_delete(self, key: str, duration_ms: float) -> None:
        """
        DELETE 작업 기록

        Args:
            key: 캐시 키
            duration_ms: 소요 시간 (밀리초)
        """
        metric = CacheMetric(
            timestamp=time.time(),
            operation="delete",
            key=key,
            hit=None,
            duration_ms=duration_ms,
        )

        self._metrics.append(metric)

    def record_error(self) -> None:
        """에러 기록"""
        self._errors += 1

    def get_stats(self, time_window_seconds: Optional[int] = None) -> CacheStats:
        """
        캐시 통계 반환

        Args:
            time_window_seconds: 통계 계산 시간 윈도우 (None = 전체)

        Returns:
            CacheStats 인스턴스
        """
        # 시간 윈도우 필터링
        if time_window_seconds:
            cutoff_time = time.time() - time_window_seconds
            metrics = [m for m in self._metrics if m.timestamp >= cutoff_time]
        else:
            metrics = list(self._metrics)

        if not metrics:
            return CacheStats()

        # GET 작업만 필터
        get_metrics = [m for m in metrics if m.operation == "get"]

        if not get_metrics:
            return CacheStats()

        # 통계 계산
        total_requests = len(get_metrics)
        hits = sum(1 for m in get_metrics if m.hit)
        misses = total_requests - hits
        hit_rate = hits / total_requests if total_requests > 0 else 0.0

        # 응답 시간 분석
        durations = sorted([m.duration_ms for m in get_metrics])
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        p95_index = int(len(durations) * 0.95)
        p99_index = int(len(durations) * 0.99)

        p95_duration = durations[p95_index] if durations else 0.0
        p99_duration = durations[p99_index] if durations else 0.0

        return CacheStats(
            total_requests=total_requests,
            hits=hits,
            misses=misses,
            hit_rate=hit_rate,
            avg_response_time_ms=avg_duration,
            p95_response_time_ms=p95_duration,
            p99_response_time_ms=p99_duration,
            errors=self._errors,
        )

    def get_tier_stats(self, time_window_seconds: Optional[int] = None) -> Dict[str, int]:
        """
        계층별 히트 통계

        Args:
            time_window_seconds: 통계 계산 시간 윈도우

        Returns:
            계층별 히트 수 딕셔너리
        """
        # 시간 윈도우 필터링
        if time_window_seconds:
            cutoff_time = time.time() - time_window_seconds
            metrics = [m for m in self._metrics if m.timestamp >= cutoff_time]
        else:
            metrics = list(self._metrics)

        # GET 작업만 필터
        get_metrics = [m for m in metrics if m.operation == "get"]

        # 계층별 카운트
        tier_counts: Dict[str, int] = {}
        for metric in get_metrics:
            tier = metric.tier or "unknown"
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        return tier_counts

    def get_hot_keys(self, top_n: int = 10) -> List[tuple[str, int]]:
        """
        핫 키 반환 (가장 많이 접근된 키)

        Args:
            top_n: 반환할 키 개수

        Returns:
            (키, 접근 횟수) 튜플 리스트
        """
        sorted_keys = sorted(self._key_access_counts.items(), key=lambda x: x[1], reverse=True)

        return sorted_keys[:top_n]

    def get_report(self, time_window_seconds: Optional[int] = None) -> str:
        """
        사람이 읽기 쉬운 리포트 생성

        Args:
            time_window_seconds: 리포트 시간 윈도우

        Returns:
            포맷된 리포트 문자열
        """
        stats = self.get_stats(time_window_seconds)
        tier_stats = self.get_tier_stats(time_window_seconds)
        hot_keys = self.get_hot_keys(top_n=5)

        lines = [
            "=" * 60,
            "Cache Performance Report",
            "=" * 60,
            f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Overall Statistics:",
            f"  Total Requests: {stats.total_requests:,}",
            f"  Hits: {stats.hits:,}",
            f"  Misses: {stats.misses:,}",
            f"  Hit Rate: {stats.hit_rate:.2%}",
            f"  Errors: {stats.errors}",
            "",
            "Response Time:",
            f"  Average: {stats.avg_response_time_ms:.2f} ms",
            f"  P95: {stats.p95_response_time_ms:.2f} ms",
            f"  P99: {stats.p99_response_time_ms:.2f} ms",
            "",
            "Tier Distribution:",
        ]

        for tier, count in sorted(tier_stats.items()):
            percentage = count / stats.total_requests * 100 if stats.total_requests > 0 else 0
            lines.append(f"  {tier.upper()}: {count:,} ({percentage:.1f}%)")

        if hot_keys:
            lines.extend(
                [
                    "",
                    "Hot Keys (Top 5):",
                ]
            )
            for key, count in hot_keys:
                lines.append(f"  {key}: {count:,} accesses")

        lines.append("=" * 60)

        return "\n".join(lines)

    def reset(self) -> None:
        """모든 메트릭 및 통계 초기화"""
        self._metrics.clear()
        self._key_access_counts.clear()
        self._errors = 0

    def _increment_key_access(self, key: str) -> None:
        """키 접근 카운트 증가"""
        self._key_access_counts[key] = self._key_access_counts.get(key, 0) + 1


# Singleton instance
_monitor_instance: Optional[CacheMonitor] = None


def get_cache_monitor() -> CacheMonitor:
    """캐시 모니터 싱글톤 반환"""
    global _monitor_instance

    if _monitor_instance is None:
        _monitor_instance = CacheMonitor()

    return _monitor_instance


def reset_cache_monitor() -> None:
    """싱글톤 초기화 (테스트용)"""
    global _monitor_instance
    _monitor_instance = None
