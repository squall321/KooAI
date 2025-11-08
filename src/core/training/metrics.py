"""
학습 메트릭 추적

학습 중 메트릭을 기록하고 분석.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MetricRecord:
    """메트릭 기록"""

    step: int
    epoch: int
    timestamp: datetime
    metrics: Dict[str, float]
    phase: str = "train"  # "train", "val", "test"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "step": self.step,
            "epoch": self.epoch,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "phase": self.phase,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricRecord":
        """딕셔너리에서 생성"""
        return cls(
            step=data["step"],
            epoch=data["epoch"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metrics=data["metrics"],
            phase=data.get("phase", "train"),
        )


class MetricsTracker:
    """
    메트릭 추적기

    학습 중 메트릭을 기록하고 분석 제공.
    """

    def __init__(self, log_dir: Path):
        """
        Args:
            log_dir: 로그 디렉토리
        """
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)

        self._records: List[MetricRecord] = []
        self._metrics_file = log_dir / "metrics.jsonl"  # JSON Lines 형식

        # 메트릭별 최적값 추적
        self._best_metrics: Dict[str, float] = {}
        self._best_steps: Dict[str, int] = {}

        # 기존 로그 로드
        self._load_records()

    def log_metrics(
        self,
        metrics: Dict[str, float],
        step: int,
        epoch: int = 0,
        phase: str = "train",
    ) -> None:
        """
        메트릭 기록

        Args:
            metrics: 메트릭 딕셔너리
            step: 현재 스텝
            epoch: 현재 에포크
            phase: 학습 단계 ("train", "val", "test")
        """
        record = MetricRecord(
            step=step,
            epoch=epoch,
            timestamp=datetime.utcnow(),
            metrics=metrics,
            phase=phase,
        )

        self._records.append(record)

        # 최적값 업데이트
        for metric_name, value in metrics.items():
            self._update_best_metric(metric_name, value, step)

        # 파일에 추가 (JSON Lines 형식)
        self._append_record(record)

    def get_metric_history(
        self, metric_name: str, phase: Optional[str] = None
    ) -> List[tuple[int, float]]:
        """
        메트릭 히스토리 조회

        Args:
            metric_name: 메트릭 이름
            phase: 학습 단계 필터 (None이면 전체)

        Returns:
            (step, value) 튜플 리스트
        """
        history = []

        for record in self._records:
            if phase and record.phase != phase:
                continue

            if metric_name in record.metrics:
                history.append((record.step, record.metrics[metric_name]))

        return history

    def get_latest_metrics(self, phase: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        최신 메트릭 조회

        Args:
            phase: 학습 단계 필터

        Returns:
            메트릭 딕셔너리 또는 None
        """
        filtered_records = [r for r in self._records if phase is None or r.phase == phase]

        if not filtered_records:
            return None

        return filtered_records[-1].metrics

    def get_best_metric(self, metric_name: str) -> Optional[tuple[float, int]]:
        """
        최적 메트릭 값 및 스텝

        Args:
            metric_name: 메트릭 이름

        Returns:
            (value, step) 튜플 또는 None
        """
        if metric_name not in self._best_metrics:
            return None

        return (
            self._best_metrics[metric_name],
            self._best_steps[metric_name],
        )

    def get_metric_summary(self, metric_name: str, phase: Optional[str] = None) -> Dict[str, float]:
        """
        메트릭 요약 통계

        Args:
            metric_name: 메트릭 이름
            phase: 학습 단계 필터

        Returns:
            요약 통계 (mean, std, min, max, latest)
        """
        history = self.get_metric_history(metric_name, phase)

        if not history:
            return {}

        values = [value for _, value in history]

        import numpy as np

        return {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "latest": values[-1],
            "count": len(values),
        }

    def get_all_metrics_summary(self, phase: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """
        모든 메트릭 요약

        Args:
            phase: 학습 단계 필터

        Returns:
            메트릭 이름 -> 요약 통계
        """
        # 모든 메트릭 이름 수집
        metric_names = set()
        for record in self._records:
            if phase is None or record.phase == phase:
                metric_names.update(record.metrics.keys())

        # 각 메트릭 요약
        summary = {}
        for metric_name in metric_names:
            summary[metric_name] = self.get_metric_summary(metric_name, phase)

        return summary

    def get_epoch_metrics(self, epoch: int, phase: Optional[str] = None) -> List[Dict[str, float]]:
        """
        특정 에포크의 메트릭

        Args:
            epoch: 에포크 번호
            phase: 학습 단계 필터

        Returns:
            메트릭 리스트
        """
        epoch_records = [
            r for r in self._records if r.epoch == epoch and (phase is None or r.phase == phase)
        ]

        return [r.metrics for r in epoch_records]

    def export_to_csv(self, output_path: Path, phase: Optional[str] = None) -> None:
        """
        메트릭을 CSV로 내보내기

        Args:
            output_path: 출력 파일 경로
            phase: 학습 단계 필터
        """
        import csv

        # 필터링된 레코드
        filtered_records = [r for r in self._records if phase is None or r.phase == phase]

        if not filtered_records:
            return

        # 모든 메트릭 키 수집
        all_keys = set()
        for record in filtered_records:
            all_keys.update(record.metrics.keys())

        # CSV 작성
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["step", "epoch", "timestamp", "phase"] + sorted(all_keys)
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for record in filtered_records:
                row = {
                    "step": record.step,
                    "epoch": record.epoch,
                    "timestamp": record.timestamp.isoformat(),
                    "phase": record.phase,
                }
                row.update(record.metrics)
                writer.writerow(row)

    def plot_metrics(
        self,
        metric_names: List[str],
        output_path: Path,
        phase: Optional[str] = None,
        title: str = "Training Metrics",
    ) -> None:
        """
        메트릭 플롯

        Args:
            metric_names: 플롯할 메트릭 이름 리스트
            output_path: 출력 이미지 경로
            phase: 학습 단계 필터
            title: 플롯 제목
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise RuntimeError("matplotlib not installed. Install with: pip install matplotlib")

        fig, axes = plt.subplots(len(metric_names), 1, figsize=(10, 4 * len(metric_names)))

        if len(metric_names) == 1:
            axes = [axes]

        for idx, metric_name in enumerate(metric_names):
            history = self.get_metric_history(metric_name, phase)

            if not history:
                continue

            steps, values = zip(*history)
            axes[idx].plot(steps, values, label=metric_name)
            axes[idx].set_xlabel("Step")
            axes[idx].set_ylabel(metric_name)
            axes[idx].set_title(f"{metric_name} over time")
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)

        plt.suptitle(title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

    def clear(self) -> None:
        """모든 메트릭 삭제"""
        self._records.clear()
        self._best_metrics.clear()
        self._best_steps.clear()

        if self._metrics_file.exists():
            self._metrics_file.unlink()

    def _update_best_metric(self, metric_name: str, value: float, step: int) -> None:
        """최적 메트릭 업데이트 (낮을수록 좋음으로 가정)"""
        if metric_name not in self._best_metrics or value < self._best_metrics[metric_name]:
            self._best_metrics[metric_name] = value
            self._best_steps[metric_name] = step

    def _append_record(self, record: MetricRecord) -> None:
        """레코드를 파일에 추가 (JSON Lines)"""
        with open(self._metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def _load_records(self) -> None:
        """기존 레코드 로드"""
        if not self._metrics_file.exists():
            return

        try:
            with open(self._metrics_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        record = MetricRecord.from_dict(data)
                        self._records.append(record)

                        # 최적값 업데이트
                        for metric_name, value in record.metrics.items():
                            self._update_best_metric(metric_name, value, record.step)

        except Exception as e:
            print(f"Failed to load metrics: {e}")
