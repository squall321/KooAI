"""
Tests for DifferenceAnalyzer
"""

import pytest
import numpy as np

from src.application.comparison.diff_analyzer import (
    DifferenceAnalyzer,
    FieldDifference,
    DifferenceType,
)


@pytest.fixture
def analyzer():
    """Create analyzer with default thresholds"""
    return DifferenceAnalyzer()


@pytest.fixture
def custom_analyzer():
    """Create analyzer with custom thresholds"""
    return DifferenceAnalyzer(
        negligible_threshold=0.02,
        small_threshold=0.10,
        moderate_threshold=0.30,
        large_threshold=0.60,
    )


def test_difference_type_enum():
    """Test DifferenceType enum"""
    assert DifferenceType.NEGLIGIBLE.value == "negligible"
    assert DifferenceType.SMALL.value == "small"
    assert DifferenceType.MODERATE.value == "moderate"
    assert DifferenceType.LARGE.value == "large"
    assert DifferenceType.CRITICAL.value == "critical"


def test_field_difference_to_dict():
    """Test FieldDifference.to_dict()"""
    diff = FieldDifference(
        field_name="temperature",
        mean_absolute_diff=5.0,
        mean_relative_diff=0.02,
        max_absolute_diff=10.0,
        max_relative_diff=0.05,
        difference_type=DifferenceType.SMALL,
        regions_with_large_diff=10,
        percentage_affected=25.5,
    )

    result = diff.to_dict()

    assert result["field_name"] == "temperature"
    assert result["mean_absolute_diff"] == 5.0
    assert result["mean_relative_diff"] == 0.02
    assert result["difference_type"] == "small"
    assert result["regions_with_large_diff"] == 10
    assert result["percentage_affected"] == 25.5


def test_analyze_field_difference_negligible(analyzer):
    """Test analysis with negligible differences"""
    field1 = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
    field2 = np.array([100.5, 200.5, 300.5, 400.5], dtype=np.float32)  # 0.5% difference

    result = analyzer.analyze_field_difference(field1, field2, "temperature")

    assert result.field_name == "temperature"
    assert result.difference_type == DifferenceType.NEGLIGIBLE
    assert result.mean_relative_diff < 0.01
    assert result.mean_absolute_diff == pytest.approx(0.5, abs=0.01)


def test_analyze_field_difference_small(analyzer):
    """Test analysis with small differences"""
    field1 = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
    field2 = np.array([103.0, 206.0, 309.0, 412.0], dtype=np.float32)  # ~3% difference

    result = analyzer.analyze_field_difference(field1, field2, "temperature")

    assert result.field_name == "temperature"
    assert result.difference_type == DifferenceType.SMALL
    assert 0.01 < result.mean_relative_diff < 0.05


def test_analyze_field_difference_moderate(analyzer):
    """Test analysis with moderate differences"""
    field1 = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
    field2 = np.array([115.0, 230.0, 345.0, 460.0], dtype=np.float32)  # ~15% difference

    result = analyzer.analyze_field_difference(field1, field2, "temperature")

    assert result.field_name == "temperature"
    assert result.difference_type == DifferenceType.MODERATE
    assert 0.05 < result.mean_relative_diff < 0.20


def test_analyze_field_difference_large(analyzer):
    """Test analysis with large differences"""
    field1 = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
    field2 = np.array([135.0, 270.0, 405.0, 540.0], dtype=np.float32)  # ~35% difference

    result = analyzer.analyze_field_difference(field1, field2, "temperature")

    assert result.field_name == "temperature"
    assert result.difference_type == DifferenceType.LARGE
    assert 0.20 < result.mean_relative_diff < 0.50


def test_analyze_field_difference_critical(analyzer):
    """Test analysis with critical differences"""
    field1 = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
    field2 = np.array([200.0, 400.0, 600.0, 800.0], dtype=np.float32)  # 100% difference

    result = analyzer.analyze_field_difference(field1, field2, "temperature")

    assert result.field_name == "temperature"
    assert result.difference_type == DifferenceType.CRITICAL
    assert result.mean_relative_diff > 0.50


def test_analyze_field_difference_metrics(analyzer):
    """Test that all metrics are calculated correctly"""
    field1 = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
    field2 = np.array([110.0, 220.0, 330.0, 440.0], dtype=np.float32)

    result = analyzer.analyze_field_difference(field1, field2, "test")

    # Check all required metrics exist
    assert result.mean_absolute_diff > 0
    assert result.mean_relative_diff > 0
    assert result.max_absolute_diff > 0
    assert result.max_relative_diff > 0
    assert isinstance(result.regions_with_large_diff, (int, np.integer))
    assert isinstance(result.percentage_affected, (float, np.floating))


def test_analyze_field_difference_critical_zones(analyzer):
    """Test critical zones detection"""
    field1 = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
    field2 = np.array([100.0, 250.0, 300.0, 500.0], dtype=np.float32)  # 2 regions with >20% diff

    result = analyzer.analyze_field_difference(field1, field2, "test")

    assert result.critical_zones is not None
    assert isinstance(result.critical_zones, np.ndarray)
    assert result.critical_zones.shape == field1.shape
    assert np.sum(result.critical_zones) == result.regions_with_large_diff


def test_analyze_all_fields(analyzer):
    """Test analyzing all fields"""
    fields1 = {
        "temperature": np.array([100.0, 200.0, 300.0], dtype=np.float32),
        "pressure": np.array([1000.0, 2000.0, 3000.0], dtype=np.float32),
        "velocity": np.array([10.0, 20.0, 30.0], dtype=np.float32),
    }

    fields2 = {
        "temperature": np.array([105.0, 210.0, 315.0], dtype=np.float32),
        "pressure": np.array([1100.0, 2200.0, 3300.0], dtype=np.float32),
        "velocity": np.array([11.0, 22.0, 33.0], dtype=np.float32),
    }

    results = analyzer.analyze_all_fields(fields1, fields2)

    assert len(results) == 3
    assert "temperature" in results
    assert "pressure" in results
    assert "velocity" in results

    for field_name, diff in results.items():
        assert isinstance(diff, FieldDifference)
        assert diff.field_name == field_name


def test_analyze_all_fields_partial_overlap(analyzer):
    """Test analyzing fields with partial overlap"""
    fields1 = {
        "temperature": np.array([100.0, 200.0], dtype=np.float32),
        "pressure": np.array([1000.0, 2000.0], dtype=np.float32),
        "velocity": np.array([10.0, 20.0], dtype=np.float32),
    }

    fields2 = {
        "temperature": np.array([105.0, 210.0], dtype=np.float32),
        "pressure": np.array([1100.0, 2200.0], dtype=np.float32),
        # velocity missing
        "density": np.array([1.0, 2.0], dtype=np.float32),  # extra field
    }

    results = analyzer.analyze_all_fields(fields1, fields2)

    # Should only include common fields
    assert len(results) == 2
    assert "temperature" in results
    assert "pressure" in results
    assert "velocity" not in results
    assert "density" not in results


def test_analyze_all_fields_shape_mismatch(analyzer):
    """Test that fields with shape mismatch are skipped"""
    fields1 = {
        "temperature": np.array([100.0, 200.0, 300.0], dtype=np.float32),
        "pressure": np.array([1000.0, 2000.0], dtype=np.float32),  # Different shape
    }

    fields2 = {
        "temperature": np.array([105.0, 210.0, 315.0], dtype=np.float32),
        "pressure": np.array([1100.0, 2200.0, 3300.0], dtype=np.float32),  # Different shape
    }

    results = analyzer.analyze_all_fields(fields1, fields2)

    # Only temperature should be analyzed (same shape)
    assert len(results) == 1
    assert "temperature" in results


def test_generate_summary_empty(analyzer):
    """Test summary generation with no differences"""
    summary = analyzer.generate_summary({})

    assert summary["status"] == "no_differences_analyzed"


def test_generate_summary(analyzer):
    """Test summary generation"""
    differences = {
        "temp1": FieldDifference(
            field_name="temp1",
            mean_absolute_diff=1.0,
            mean_relative_diff=0.005,
            max_absolute_diff=2.0,
            max_relative_diff=0.01,
            difference_type=DifferenceType.NEGLIGIBLE,
            regions_with_large_diff=0,
            percentage_affected=0.0,
        ),
        "temp2": FieldDifference(
            field_name="temp2",
            mean_absolute_diff=10.0,
            mean_relative_diff=0.15,
            max_absolute_diff=20.0,
            max_relative_diff=0.30,
            difference_type=DifferenceType.MODERATE,
            regions_with_large_diff=10,
            percentage_affected=25.0,
        ),
        "temp3": FieldDifference(
            field_name="temp3",
            mean_absolute_diff=50.0,
            mean_relative_diff=0.60,
            max_absolute_diff=100.0,
            max_relative_diff=1.0,
            difference_type=DifferenceType.CRITICAL,
            regions_with_large_diff=50,
            percentage_affected=75.0,
        ),
    }

    summary = analyzer.generate_summary(differences)

    assert summary["total_fields_compared"] == 3
    assert "difference_type_counts" in summary
    assert summary["difference_type_counts"]["negligible"] == 1
    assert summary["difference_type_counts"]["moderate"] == 1
    assert summary["difference_type_counts"]["critical"] == 1

    assert "top_different_fields" in summary
    assert len(summary["top_different_fields"]) == 3

    # Should be sorted by mean_relative_diff (descending)
    assert summary["top_different_fields"][0]["field_name"] == "temp3"
    assert summary["top_different_fields"][1]["field_name"] == "temp2"

    assert "critical_fields" in summary
    assert "temp3" in summary["critical_fields"]

    assert "overall_status" in summary


def test_generate_summary_overall_status_critical(analyzer):
    """Test overall status with critical differences"""
    differences = {
        "temp1": FieldDifference(
            field_name="temp1",
            mean_absolute_diff=50.0,
            mean_relative_diff=0.60,
            max_absolute_diff=100.0,
            max_relative_diff=1.0,
            difference_type=DifferenceType.CRITICAL,
            regions_with_large_diff=50,
            percentage_affected=75.0,
        ),
    }

    summary = analyzer.generate_summary(differences)
    assert summary["overall_status"] == "critical_differences_found"


def test_generate_summary_overall_status_significant(analyzer):
    """Test overall status with significant differences"""
    differences = {
        "temp1": FieldDifference(
            field_name="temp1",
            mean_absolute_diff=30.0,
            mean_relative_diff=0.35,
            max_absolute_diff=60.0,
            max_relative_diff=0.7,
            difference_type=DifferenceType.LARGE,
            regions_with_large_diff=30,
            percentage_affected=60.0,
        ),
        "temp2": FieldDifference(
            field_name="temp2",
            mean_absolute_diff=25.0,
            mean_relative_diff=0.30,
            max_absolute_diff=50.0,
            max_relative_diff=0.6,
            difference_type=DifferenceType.LARGE,
            regions_with_large_diff=25,
            percentage_affected=50.0,
        ),
    }

    summary = analyzer.generate_summary(differences)
    assert summary["overall_status"] == "significant_differences_found"


def test_generate_summary_overall_status_some(analyzer):
    """Test overall status with some differences"""
    differences = {
        "temp1": FieldDifference(
            field_name="temp1",
            mean_absolute_diff=1.0,
            mean_relative_diff=0.005,
            max_absolute_diff=2.0,
            max_relative_diff=0.01,
            difference_type=DifferenceType.NEGLIGIBLE,
            regions_with_large_diff=0,
            percentage_affected=0.0,
        ),
        "temp2": FieldDifference(
            field_name="temp2",
            mean_absolute_diff=20.0,
            mean_relative_diff=0.25,
            max_absolute_diff=40.0,
            max_relative_diff=0.5,
            difference_type=DifferenceType.LARGE,
            regions_with_large_diff=20,
            percentage_affected=40.0,
        ),
    }

    summary = analyzer.generate_summary(differences)
    assert summary["overall_status"] == "some_differences_found"


def test_generate_summary_overall_status_minor(analyzer):
    """Test overall status with only minor differences"""
    differences = {
        "temp1": FieldDifference(
            field_name="temp1",
            mean_absolute_diff=1.0,
            mean_relative_diff=0.005,
            max_absolute_diff=2.0,
            max_relative_diff=0.01,
            difference_type=DifferenceType.NEGLIGIBLE,
            regions_with_large_diff=0,
            percentage_affected=0.0,
        ),
        "temp2": FieldDifference(
            field_name="temp2",
            mean_absolute_diff=3.0,
            mean_relative_diff=0.03,
            max_absolute_diff=6.0,
            max_relative_diff=0.06,
            difference_type=DifferenceType.SMALL,
            regions_with_large_diff=0,
            percentage_affected=0.0,
        ),
    }

    summary = analyzer.generate_summary(differences)
    assert summary["overall_status"] == "minor_differences_only"


def test_identify_outlier_regions(analyzer):
    """Test outlier region identification"""
    # Create fields with mostly small differences but a few outliers
    np.random.seed(42)
    field1 = np.random.uniform(100, 200, 100).astype(np.float32)
    field2 = field1 + np.random.normal(0, 1, 100).astype(np.float32)

    # Add some outliers
    field2[0] += 50  # Large positive outlier
    field2[1] -= 50  # Large negative outlier

    outlier_mask, statistics = analyzer.identify_outlier_regions(field1, field2, threshold_std=3.0)

    assert isinstance(outlier_mask, np.ndarray)
    assert outlier_mask.shape == field1.shape
    assert statistics["num_outliers"] > 0
    assert statistics["percentage_outliers"] > 0
    assert statistics["threshold_std"] == 3.0
    assert "mean_difference" in statistics
    assert "std_difference" in statistics


def test_identify_outlier_regions_no_outliers(analyzer):
    """Test outlier identification with no outliers"""
    field1 = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
    field2 = np.array([101.0, 201.0, 301.0, 401.0], dtype=np.float32)  # Uniform small difference

    outlier_mask, statistics = analyzer.identify_outlier_regions(field1, field2, threshold_std=3.0)

    # With uniform differences, should find no outliers
    assert statistics["num_outliers"] == 0
    assert statistics["percentage_outliers"] == 0.0


def test_custom_thresholds(custom_analyzer):
    """Test analyzer with custom thresholds"""
    field1 = np.array([100.0, 200.0, 300.0], dtype=np.float32)
    field2 = np.array([103.0, 206.0, 309.0], dtype=np.float32)  # 3% difference

    result = custom_analyzer.analyze_field_difference(field1, field2, "test")

    # With custom thresholds (negligible < 2%, small < 10%), 3% should be SMALL
    assert result.difference_type == DifferenceType.SMALL


def test_edge_case_zero_denominator(analyzer):
    """Test edge case where field1 has zero values"""
    field1 = np.array([0.0, 100.0, 200.0, 300.0], dtype=np.float32)
    field2 = np.array([10.0, 110.0, 220.0, 330.0], dtype=np.float32)

    # Should handle zero values without division by zero error
    result = analyzer.analyze_field_difference(field1, field2, "test")

    assert result is not None
    assert not np.isnan(result.mean_relative_diff)
    assert not np.isinf(result.mean_relative_diff)


def test_edge_case_identical_fields(analyzer):
    """Test edge case with identical fields"""
    field1 = np.array([100.0, 200.0, 300.0], dtype=np.float32)
    field2 = field1.copy()

    result = analyzer.analyze_field_difference(field1, field2, "test")

    assert result.mean_absolute_diff == pytest.approx(0.0, abs=1e-6)
    assert result.mean_relative_diff == pytest.approx(0.0, abs=1e-6)
    assert result.difference_type == DifferenceType.NEGLIGIBLE
    assert result.regions_with_large_diff == 0


def test_edge_case_negative_values(analyzer):
    """Test edge case with negative values"""
    field1 = np.array([-100.0, -50.0, 0.0, 50.0], dtype=np.float32)
    field2 = np.array([-90.0, -45.0, 5.0, 55.0], dtype=np.float32)

    result = analyzer.analyze_field_difference(field1, field2, "test")

    assert result is not None
    assert result.mean_absolute_diff > 0
    assert result.mean_relative_diff >= 0


def test_large_dataset(analyzer):
    """Test with large dataset"""
    np.random.seed(42)
    field1 = np.random.uniform(100, 200, 100000).astype(np.float32)
    field2 = field1 + np.random.normal(0, 5, 100000).astype(np.float32)

    result = analyzer.analyze_field_difference(field1, field2, "large_test")

    assert result is not None
    assert result.mean_relative_diff > 0
    assert isinstance(result.difference_type, DifferenceType)
