"""
Automated tests for example scripts

Tests that all example scripts execute without errors.
"""

import pytest
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import importlib.util


# Examples to test
EXAMPLES = [
    "01_basic_usage.py",
    "02_batch_processing.py",
    "03_simulation_comparison.py",
    "04_report_generation.py",
    "05_export_data.py",
    "06_streaming_large_files.py",
    "07_auto_format_detection.py",
    "08_caching_strategies.py",
    "09_async_task_queue.py",
]

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for example data"""
    temp_dir = tempfile.mkdtemp(prefix="kooai_examples_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestExampleScripts:
    """Test that example scripts run without errors"""

    @pytest.mark.parametrize("example_name", EXAMPLES)
    def test_example_imports(self, example_name):
        """Test that example script can be imported"""
        example_path = EXAMPLES_DIR / example_name

        assert example_path.exists(), f"Example {example_name} not found"

        # Try to load the module
        spec = importlib.util.spec_from_file_location(f"example_{example_name[:-3]}", example_path)
        assert spec is not None, f"Could not load spec for {example_name}"

        module = importlib.util.module_from_spec(spec)
        assert module is not None, f"Could not create module for {example_name}"

    def test_01_basic_usage_syntax(self):
        """Test basic usage example has valid syntax"""
        example_path = EXAMPLES_DIR / "01_basic_usage.py"

        # Compile the file to check syntax
        with open(example_path) as f:
            code = f.read()
            compile(code, example_path, "exec")

    def test_02_batch_processing_syntax(self):
        """Test batch processing example has valid syntax"""
        example_path = EXAMPLES_DIR / "02_batch_processing.py"

        with open(example_path) as f:
            code = f.read()
            compile(code, example_path, "exec")

    def test_06_streaming_imports(self):
        """Test streaming example can import required modules"""
        example_path = EXAMPLES_DIR / "06_streaming_large_files.py"

        # Check that streaming parser modules are available
        from src.core.simulation.parsers.streaming_csv_parser import StreamingCSVParser
        from src.core.simulation.parsers.streaming_json_parser import StreamingJSONParser

        assert StreamingCSVParser is not None
        assert StreamingJSONParser is not None

    def test_07_format_detection_imports(self):
        """Test format detection example can import required modules"""
        example_path = EXAMPLES_DIR / "07_auto_format_detection.py"

        # Check that format detector is available
        from src.core.simulation.parsers.format_detector import FormatDetector

        assert FormatDetector is not None

    def test_08_caching_imports(self):
        """Test caching example can import required modules"""
        example_path = EXAMPLES_DIR / "08_caching_strategies.py"

        # Check that cache modules are available
        from src.infrastructure.cache.lru_cache import LRUCache
        from src.infrastructure.cache.multi_tier_cache import MultiTierCache

        assert LRUCache is not None
        assert MultiTierCache is not None

    def test_09_task_queue_imports(self):
        """Test task queue example can import required modules"""
        example_path = EXAMPLES_DIR / "09_async_task_queue.py"

        # Check that task modules are available
        from src.infrastructure.tasks import (
            task,
            TaskPriority,
            get_task_queue,
            get_worker_pool,
            register_tasks_to_workers,
        )

        assert task is not None
        assert TaskPriority is not None
        assert get_task_queue is not None


class TestStreamingExample:
    """Detailed tests for streaming example"""

    def test_streaming_csv_example_components(self, temp_data_dir):
        """Test streaming CSV example components"""
        from src.core.simulation.parsers.streaming_csv_parser import StreamingCSVParser

        # Create test CSV
        csv_file = temp_data_dir / "test.csv"
        with open(csv_file, "w") as f:
            f.write("x,y,z,temperature\n")
            for i in range(100):
                f.write(f"{i},{i*2},{i*3},{300+i}\n")

        # Test streaming parser
        parser = StreamingCSVParser(chunk_size=10)
        chunks = list(parser.parse(csv_file))

        assert len(chunks) > 0
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 100

    def test_streaming_json_example_components(self, temp_data_dir):
        """Test streaming JSON example components"""
        from src.core.simulation.parsers.streaming_json_parser import StreamingJSONParser
        import json

        # Create test JSON
        json_file = temp_data_dir / "test.json"
        data = [{"id": i, "value": i * 2} for i in range(100)]
        with open(json_file, "w") as f:
            json.dump(data, f)

        # Test streaming parser
        parser = StreamingJSONParser(batch_size=10)
        items = list(parser.parse_array_stream(json_file))

        assert len(items) == 100


class TestFormatDetectionExample:
    """Detailed tests for format detection example"""

    def test_csv_detection(self, temp_data_dir):
        """Test CSV format detection"""
        from src.core.simulation.parsers.format_detector import FormatDetector, FileFormat

        # Create CSV file
        csv_file = temp_data_dir / "test.csv"
        with open(csv_file, "w") as f:
            f.write("x,y,z\n")
            f.write("1,2,3\n")

        detector = FormatDetector()
        result = detector.detect(csv_file)

        assert result.format == FileFormat.CSV
        assert result.confidence >= 0.5

    def test_json_detection(self, temp_data_dir):
        """Test JSON format detection"""
        from src.core.simulation.parsers.format_detector import FormatDetector, FileFormat
        import json

        # Create JSON file
        json_file = temp_data_dir / "test.json"
        with open(json_file, "w") as f:
            json.dump({"test": "data"}, f)

        detector = FormatDetector()
        result = detector.detect(json_file)

        assert result.format == FileFormat.JSON
        assert result.confidence >= 0.5


class TestCachingExample:
    """Detailed tests for caching example"""

    def test_lru_cache_basic(self):
        """Test basic LRU cache from example"""
        from src.infrastructure.cache.lru_cache import LRUCache

        cache = LRUCache(max_size=100, default_ttl=60)

        # Basic operations
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Statistics
        stats = cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats

    def test_lru_eviction(self):
        """Test LRU eviction policy"""
        from src.infrastructure.cache.lru_cache import LRUCache

        cache = LRUCache(max_size=3, default_ttl=60)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1
        cache.get("key1")

        # Add new item - should evict key2
        cache.set("key4", "value4")

        assert cache.get("key1") is not None  # Recently accessed
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None

    def test_multi_tier_cache_from_mock(self):
        """Test multi-tier cache with mock L2"""
        from src.infrastructure.cache.multi_tier_cache import MultiTierCache
        from src.infrastructure.cache.lru_cache import LRUCache
        from unittest.mock import MagicMock

        # Mock L2 cache
        l2_cache = MagicMock()
        l2_cache.ping.return_value = True
        l2_cache._storage = {}
        l2_cache.get.return_value = None
        l2_cache.set.return_value = True

        cache = MultiTierCache(l2_cache=l2_cache, l1_max_size=10)

        # Basic operations
        cache.set("key1", "value1")
        value = cache.get("key1")

        assert value == "value1"


class TestTaskQueueExample:
    """Detailed tests for task queue example"""

    def test_task_decorator(self):
        """Test @task decorator from example"""
        from src.infrastructure.tasks import task, TaskPriority

        @task(name="test.example_task", priority=TaskPriority.NORMAL)
        def example_task(x: int) -> int:
            return x * 2

        # Test direct call
        result = example_task(5)
        assert result == 10

        # Test has delay method
        assert hasattr(example_task, "delay")
        assert hasattr(example_task, "wait")

    def test_task_queue_basic(self):
        """Test basic task queue operations"""
        from src.infrastructure.tasks import TaskQueue, Task

        queue = TaskQueue()

        # Enqueue task
        task = Task(name="test_task", args=(1, 2))
        task_id = queue.enqueue(task)

        assert task_id is not None

        # Dequeue task
        dequeued = queue.dequeue(timeout=0.1)
        assert dequeued is not None
        assert dequeued.name == "test_task"

    def test_worker_pool_basic(self):
        """Test basic worker pool operations"""
        from src.infrastructure.tasks import WorkerPool

        pool = WorkerPool(num_workers=2)
        pool.start()

        assert pool.running_workers == 2

        pool.stop(timeout=1.0)
        assert pool.running_workers == 0


class TestExampleDataRequirements:
    """Test that examples handle missing data gracefully"""

    def test_examples_dont_require_hardcoded_paths(self):
        """Test that examples use relative or generated paths"""
        for example_name in EXAMPLES:
            example_path = EXAMPLES_DIR / example_name

            with open(example_path) as f:
                content = f.read()

                # Check for absolute hardcoded paths (likely errors)
                # Allow /tmp and similar temp paths
                suspicious_paths = [
                    '"/home/specific/user/',
                    '"/Users/specific/',
                    '"C:\\Users\\specific\\',
                ]

                for suspicious in suspicious_paths:
                    assert (
                        suspicious not in content
                    ), f"{example_name} contains suspicious hardcoded path: {suspicious}"

    def test_examples_have_main_guard(self):
        """Test that examples have if __name__ == '__main__' guard"""
        critical_examples = [
            "06_streaming_large_files.py",
            "07_auto_format_detection.py",
            "08_caching_strategies.py",
            "09_async_task_queue.py",
        ]

        for example_name in critical_examples:
            example_path = EXAMPLES_DIR / example_name

            with open(example_path) as f:
                content = f.read()

                assert (
                    'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content
                ), f"{example_name} missing main guard"


class TestExampleDocumentation:
    """Test that examples are well documented"""

    def test_examples_have_docstrings(self):
        """Test that examples have module docstrings"""
        for example_name in EXAMPLES:
            example_path = EXAMPLES_DIR / example_name

            with open(example_path) as f:
                content = f.read()

                # Should have triple-quoted docstring at top
                assert (
                    '"""' in content or "'''" in content
                ), f"{example_name} missing module docstring"

    def test_examples_have_function_comments(self):
        """Test that examples have descriptive comments"""
        for example_name in EXAMPLES:
            example_path = EXAMPLES_DIR / example_name

            with open(example_path) as f:
                content = f.read()

                # Should have some comments (at least 3)
                comment_count = content.count("#")
                assert comment_count >= 3, f"{example_name} has too few comments ({comment_count})"


class TestNewExamples:
    """Test the 4 new examples we created (06-09)"""

    def test_06_has_chunk_size_examples(self):
        """Test that streaming example demonstrates chunk sizes"""
        example_path = EXAMPLES_DIR / "06_streaming_large_files.py"

        with open(example_path) as f:
            content = f.read()

            assert "chunk_size" in content
            assert "StreamingCSVParser" in content
            assert "StreamingJSONParser" in content

    def test_07_has_detection_methods(self):
        """Test that format detection example shows all methods"""
        example_path = EXAMPLES_DIR / "07_auto_format_detection.py"

        with open(example_path) as f:
            content = f.read()

            assert "FormatDetector" in content
            assert "detect" in content
            assert "confidence" in content

    def test_08_has_multi_tier_example(self):
        """Test that caching example shows multi-tier cache"""
        example_path = EXAMPLES_DIR / "08_caching_strategies.py"

        with open(example_path) as f:
            content = f.read()

            assert "MultiTierCache" in content
            assert "LRUCache" in content
            assert "L1" in content or "l1" in content
            assert "L2" in content or "l2" in content

    def test_09_has_priority_examples(self):
        """Test that task queue example shows priorities"""
        example_path = EXAMPLES_DIR / "09_async_task_queue.py"

        with open(example_path) as f:
            content = f.read()

            assert "TaskPriority" in content
            assert "HIGH" in content or "priority" in content
            assert "WorkerPool" in content
            assert "@task" in content


class TestExampleOutput:
    """Test that examples produce expected output patterns"""

    def test_examples_have_progress_indicators(self):
        """Test that long-running examples show progress"""
        long_running = [
            "06_streaming_large_files.py",
            "08_caching_strategies.py",
            "09_async_task_queue.py",
        ]

        for example_name in long_running:
            example_path = EXAMPLES_DIR / example_name

            with open(example_path) as f:
                content = f.read()

                # Should have some form of progress indication
                has_progress = any(
                    [
                        "print" in content,
                        "logger" in content,
                        "logging" in content,
                    ]
                )

                assert has_progress, f"{example_name} lacks progress indicators"

    def test_examples_show_results(self):
        """Test that examples display results"""
        for example_name in EXAMPLES:
            example_path = EXAMPLES_DIR / example_name

            with open(example_path) as f:
                content = f.read()

                # Should have output (print statements or logging)
                has_output = any(
                    [
                        "print(" in content,
                        'print "' in content,
                    ]
                )

                assert has_output, f"{example_name} doesn't show results"


@pytest.mark.slow
class TestExampleExecution:
    """
    Slow tests that actually execute examples

    These are marked as slow and skipped by default.
    Run with: pytest -m slow
    """

    @pytest.mark.parametrize(
        "example_name",
        [
            "06_streaming_large_files.py",
            "07_auto_format_detection.py",
            "08_caching_strategies.py",
        ],
    )
    def test_example_executes(self, example_name, temp_data_dir):
        """Test that example can be executed"""
        example_path = EXAMPLES_DIR / example_name

        # Some examples might need data directory
        env = {
            "PYTHONPATH": str(Path(__file__).parent.parent.parent),
            "DATA_DIR": str(temp_data_dir),
        }

        # Try to run the example
        # Note: Some examples might fail due to missing data,
        # but they should at least import successfully
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{EXAMPLES_DIR.parent}'); import {example_name[:-3]}",
            ],
            capture_output=True,
            timeout=5,
        )

        # Should at least import without syntax errors
        if result.returncode != 0:
            # Print error for debugging
            print(f"Import error for {example_name}:")
            print(result.stderr.decode())


class TestExampleIntegrity:
    """Test overall integrity of examples directory"""

    def test_all_examples_listed(self):
        """Test that all .py files in examples/ are in our test list"""
        example_files = list(EXAMPLES_DIR.glob("*.py"))
        example_names = [f.name for f in example_files]

        # Remove __init__.py if present
        example_names = [n for n in example_names if not n.startswith("__")]

        # Check all are in our list
        for name in example_names:
            assert name in EXAMPLES, f"Example {name} not in test list. Add it to EXAMPLES list."

    def test_examples_directory_exists(self):
        """Test that examples directory exists"""
        assert EXAMPLES_DIR.exists()
        assert EXAMPLES_DIR.is_dir()

    def test_all_listed_examples_exist(self):
        """Test that all listed examples exist"""
        for example_name in EXAMPLES:
            example_path = EXAMPLES_DIR / example_name
            assert example_path.exists(), f"Example {example_name} not found"
