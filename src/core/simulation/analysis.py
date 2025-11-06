"""
시뮬레이션 결과 분석

시뮬레이션 결과 통계 분석 및 메트릭 계산.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from .models import (
    FieldData,
    FieldType,
    SimulationMetrics,
    SimulationResult,
    TimeStepData,
)


class ResultAnalyzer:
    """
    시뮬레이션 결과 분석기

    통계 분석, 메트릭 계산, 이상 탐지 등.
    """

    @staticmethod
    def compute_field_statistics(field: FieldData) -> Dict[str, float]:
        """
        필드 통계 계산

        Args:
            field: 필드 데이터

        Returns:
            통계 딕셔너리 (min, max, mean, std, percentiles)
        """
        if field.field_type == FieldType.SCALAR:
            data = field.data
        elif field.field_type == FieldType.VECTOR:
            # 벡터 크기
            data = np.linalg.norm(field.data, axis=1)
        else:
            # 텐서는 Frobenius norm
            data = np.linalg.norm(field.data.reshape(len(field.data), -1), axis=1)

        return {
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "median": float(np.median(data)),
            "percentile_25": float(np.percentile(data, 25)),
            "percentile_75": float(np.percentile(data, 75)),
            "percentile_95": float(np.percentile(data, 95)),
            "percentile_99": float(np.percentile(data, 99)),
        }

    @staticmethod
    def compute_timestep_metrics(
        result: SimulationResult,
        timestep: TimeStepData,
    ) -> SimulationMetrics:
        """
        타임스텝 메트릭 계산

        Args:
            result: 시뮬레이션 결과
            timestep: 타임스텝

        Returns:
            SimulationMetrics
        """
        metrics = SimulationMetrics(
            result_name=result.name,
            timestep=timestep.step,
            time=timestep.time,
        )

        # 각 필드의 통계
        for field_name, field in timestep.fields.items():
            stats = ResultAnalyzer.compute_field_statistics(field)
            metrics.add_field_stats(
                field_name=field_name,
                min_val=stats["min"],
                max_val=stats["max"],
                mean_val=stats["mean"],
                std_val=stats["std"],
            )

        return metrics

    @staticmethod
    def find_extreme_values(
        field: FieldData,
        n_extremes: int = 10,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        극값 찾기 (최대값, 최솟값)

        Args:
            field: 필드 데이터
            n_extremes: 찾을 극값 개수

        Returns:
            (최댓값 인덱스, 최솟값 인덱스)
        """
        if field.field_type == FieldType.SCALAR:
            data = field.data
        elif field.field_type == FieldType.VECTOR:
            data = np.linalg.norm(field.data, axis=1)
        else:
            data = np.linalg.norm(field.data.reshape(len(field.data), -1), axis=1)

        # n_extremes가 데이터 크기보다 크면 조정
        n_extremes = min(n_extremes, len(data))

        # 최댓값 인덱스
        if n_extremes < len(data):
            max_indices = np.argpartition(data, -n_extremes)[-n_extremes:]
            max_indices = max_indices[np.argsort(data[max_indices])[::-1]]

            # 최솟값 인덱스
            min_indices = np.argpartition(data, n_extremes)[:n_extremes]
            min_indices = min_indices[np.argsort(data[min_indices])]
        else:
            # 모든 데이터를 정렬
            sorted_indices = np.argsort(data)
            max_indices = sorted_indices[::-1]
            min_indices = sorted_indices

        return max_indices, min_indices

    @staticmethod
    def detect_outliers(
        field: FieldData,
        threshold: float = 3.0,
    ) -> np.ndarray:
        """
        이상치 탐지 (Z-score 기반)

        Args:
            field: 필드 데이터
            threshold: Z-score 임계값 (기본: 3.0)

        Returns:
            이상치 인덱스 배열
        """
        if field.field_type == FieldType.SCALAR:
            data = field.data
        elif field.field_type == FieldType.VECTOR:
            data = np.linalg.norm(field.data, axis=1)
        else:
            data = np.linalg.norm(field.data.reshape(len(field.data), -1), axis=1)

        mean = np.mean(data)
        std = np.std(data)

        if std < 1e-10:
            return np.array([])

        z_scores = np.abs((data - mean) / std)
        outliers = np.where(z_scores > threshold)[0]

        return outliers

    @staticmethod
    def compute_gradient(
        field: FieldData,
        vertices: np.ndarray,
        faces: np.ndarray,
    ) -> np.ndarray:
        """
        스칼라 필드의 그래디언트 계산 (간단한 finite difference)

        Args:
            field: 스칼라 필드
            vertices: 꼭짓점
            faces: 면

        Returns:
            그래디언트 벡터 (N x 3)
        """
        if field.field_type != FieldType.SCALAR:
            raise ValueError("Gradient only applicable to scalar fields")

        n_vertices = len(vertices)
        gradients = np.zeros((n_vertices, 3))
        counts = np.zeros(n_vertices)

        # 각 면에서 그래디언트 추정
        for face in faces:
            v1, v2, v3 = face

            # 삼각형 꼭짓점
            p1 = vertices[v1]
            p2 = vertices[v2]
            p3 = vertices[v3]

            # 스칼라 값
            s1 = field.data[v1]
            s2 = field.data[v2]
            s3 = field.data[v3]

            # 엣지 벡터
            e1 = p2 - p1
            e2 = p3 - p1

            # 스칼라 차이
            ds1 = s2 - s1
            ds2 = s3 - s1

            # 법선
            normal = np.cross(e1, e2)
            area = np.linalg.norm(normal)

            if area < 1e-10:
                continue

            # 그래디언트 (간단한 추정)
            # ∇s ≈ (ds1 * e1 + ds2 * e2) / area
            grad = (ds1 * e1 + ds2 * e2) / area

            # 각 꼭짓점에 누적
            gradients[v1] += grad
            gradients[v2] += grad
            gradients[v3] += grad

            counts[v1] += 1
            counts[v2] += 1
            counts[v3] += 1

        # 평균
        mask = counts > 0
        gradients[mask] /= counts[mask, np.newaxis]

        return gradients

    @staticmethod
    def compute_field_histogram(
        field: FieldData,
        bins: int = 50,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        필드 히스토그램 계산

        Args:
            field: 필드 데이터
            bins: 빈 개수

        Returns:
            (히스토그램 값, 빈 경계)
        """
        if field.field_type == FieldType.SCALAR:
            data = field.data
        elif field.field_type == FieldType.VECTOR:
            data = np.linalg.norm(field.data, axis=1)
        else:
            data = np.linalg.norm(field.data.reshape(len(field.data), -1), axis=1)

        hist, edges = np.histogram(data, bins=bins)

        return hist, edges

    @staticmethod
    def compare_timesteps(
        timestep1: TimeStepData,
        timestep2: TimeStepData,
        field_name: str,
    ) -> Dict[str, float]:
        """
        타임스텝 간 필드 비교

        Args:
            timestep1: 타임스텝 1
            timestep2: 타임스텝 2
            field_name: 필드 이름

        Returns:
            비교 메트릭 (max_diff, mean_diff, rms_diff)
        """
        field1 = timestep1.get_field(field_name)
        field2 = timestep2.get_field(field_name)

        if not field1 or not field2:
            raise ValueError(f"Field {field_name} not found in both timesteps")

        if field1.field_type != field2.field_type:
            raise ValueError("Field types do not match")

        # 데이터 추출
        if field1.field_type == FieldType.SCALAR:
            data1 = field1.data
            data2 = field2.data
        elif field1.field_type == FieldType.VECTOR:
            data1 = np.linalg.norm(field1.data, axis=1)
            data2 = np.linalg.norm(field2.data, axis=1)
        else:
            data1 = np.linalg.norm(field1.data.reshape(len(field1.data), -1), axis=1)
            data2 = np.linalg.norm(field2.data.reshape(len(field2.data), -1), axis=1)

        # 차이
        diff = data2 - data1

        return {
            "max_diff": float(np.max(np.abs(diff))),
            "mean_diff": float(np.mean(diff)),
            "rms_diff": float(np.sqrt(np.mean(diff**2))),
            "relative_change": float(np.mean(np.abs(diff) / (np.abs(data1) + 1e-10))),
        }

    @staticmethod
    def compute_convergence_metrics(
        result: SimulationResult,
        field_name: str,
    ) -> List[Dict[str, float]]:
        """
        수렴성 메트릭 계산 (시간에 따른 변화율)

        Args:
            result: 시뮬레이션 결과
            field_name: 필드 이름

        Returns:
            타임스텝별 변화율 리스트
        """
        if result.num_timesteps < 2:
            return []

        convergence = []

        for i in range(1, result.num_timesteps):
            ts1 = result.timesteps[i - 1]
            ts2 = result.timesteps[i]

            metrics = ResultAnalyzer.compare_timesteps(ts1, ts2, field_name)

            convergence.append({
                "timestep": ts2.step,
                "time": ts2.time,
                "rms_change": metrics["rms_diff"],
                "relative_change": metrics["relative_change"],
            })

        return convergence


class SpatialAnalyzer:
    """
    공간 분석

    메시 기반 공간 분석.
    """

    @staticmethod
    def compute_region_statistics(
        field: FieldData,
        vertices: np.ndarray,
        region_mask: np.ndarray,
    ) -> Dict[str, float]:
        """
        특정 영역의 통계

        Args:
            field: 필드 데이터
            vertices: 꼭짓점
            region_mask: 영역 마스크 (bool 배열)

        Returns:
            영역 통계
        """
        if field.field_type == FieldType.SCALAR:
            data = field.data[region_mask]
        elif field.field_type == FieldType.VECTOR:
            data = np.linalg.norm(field.data[region_mask], axis=1)
        else:
            region_data = field.data[region_mask]
            data = np.linalg.norm(region_data.reshape(len(region_data), -1), axis=1)

        if len(data) == 0:
            return {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "std": 0.0,
                "count": 0,
            }

        return {
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "count": len(data),
        }

    @staticmethod
    def find_region_by_value(
        field: FieldData,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> np.ndarray:
        """
        값 범위로 영역 찾기

        Args:
            field: 필드 데이터
            min_value: 최솟값
            max_value: 최댓값

        Returns:
            영역 마스크
        """
        if field.field_type == FieldType.SCALAR:
            data = field.data
        elif field.field_type == FieldType.VECTOR:
            data = np.linalg.norm(field.data, axis=1)
        else:
            data = np.linalg.norm(field.data.reshape(len(field.data), -1), axis=1)

        mask = np.ones(len(data), dtype=bool)

        if min_value is not None:
            mask &= data >= min_value

        if max_value is not None:
            mask &= data <= max_value

        return mask
