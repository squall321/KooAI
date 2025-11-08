"""
Performance benchmark tests

Run specific performance benchmarks without full load testing
"""

import time
import statistics
import sys
from pathlib import Path
from typing import List, Dict, Any
import requests
from io import BytesIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class PerformanceBenchmark:
    """Run performance benchmarks"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}

    def run_all_benchmarks(self):
        """Run all benchmark tests"""
        print("=" * 60)
        print("PERFORMANCE BENCHMARKS")
        print("=" * 60)
        print()

        benchmarks = [
            ("Health Check", self.benchmark_health_check),
            ("List Simulations", self.benchmark_list_simulations),
            ("Upload Small File (50 points)", lambda: self.benchmark_upload(50)),
            ("Upload Medium File (500 points)", lambda: self.benchmark_upload(500)),
            ("Upload Large File (5000 points)", lambda: self.benchmark_upload(5000)),
            ("Field Analysis", self.benchmark_field_analysis),
            ("Concurrent Requests", self.benchmark_concurrent_requests),
        ]

        for name, benchmark_func in benchmarks:
            print(f"\n{name}:")
            print("-" * 60)
            try:
                result = benchmark_func()
                self.results[name] = result
                self._print_stats(result)
            except Exception as e:
                print(f"❌ Error: {e}")
                self.results[name] = {"error": str(e)}

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        self._print_summary()

    def benchmark_health_check(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark health check endpoint"""
        times = []
        errors = 0

        for _ in range(iterations):
            start = time.time()
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                elapsed = (time.time() - start) * 1000  # Convert to ms
                times.append(elapsed)
                if response.status_code != 200:
                    errors += 1
            except Exception:
                errors += 1
                times.append(5000)  # Timeout as 5000ms

        return self._calculate_stats(times, errors, iterations)

    def benchmark_list_simulations(self, iterations: int = 50) -> Dict[str, Any]:
        """Benchmark list simulations endpoint"""
        times = []
        errors = 0

        for _ in range(iterations):
            start = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/v1/simulations", timeout=10)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                if response.status_code != 200:
                    errors += 1
            except Exception:
                errors += 1
                times.append(10000)

        return self._calculate_stats(times, errors, iterations)

    def benchmark_upload(self, points: int = 100, iterations: int = 10) -> Dict[str, Any]:
        """Benchmark file upload"""
        times = []
        errors = 0

        for i in range(iterations):
            csv_data = self._generate_csv(points)
            files = {"file": ("test.csv", csv_data, "text/csv")}
            data = {"name": f"Benchmark {i}"}

            start = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/simulations/upload", files=files, data=data, timeout=30
                )
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                if response.status_code != 200:
                    errors += 1
            except Exception:
                errors += 1
                times.append(30000)

        return self._calculate_stats(times, errors, iterations, extra={"points": points})

    def benchmark_field_analysis(self, iterations: int = 20) -> Dict[str, Any]:
        """Benchmark field analysis"""
        # First upload a simulation
        csv_data = self._generate_csv(1000)
        files = {"file": ("bench.csv", csv_data, "text/csv")}
        response = requests.post(
            f"{self.base_url}/api/v1/simulations/upload", files=files, data={"name": "Benchmark"}
        )

        if response.status_code != 200:
            return {"error": "Failed to upload test simulation"}

        sim_id = response.json()["simulation_id"]

        times = []
        errors = 0

        for _ in range(iterations):
            start = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/simulations/{sim_id}/analyze",
                    json={"field_name": "temperature", "include_extremes": True},
                    timeout=15,
                )
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                if response.status_code != 200:
                    errors += 1
            except Exception:
                errors += 1
                times.append(15000)

        return self._calculate_stats(times, errors, iterations)

    def benchmark_concurrent_requests(self, concurrent: int = 10) -> Dict[str, Any]:
        """Benchmark concurrent requests"""
        import concurrent.futures

        def make_request():
            start = time.time()
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                elapsed = (time.time() - start) * 1000
                return elapsed, response.status_code == 200
            except Exception:
                return 5000, False

        times = []
        errors = 0

        start_all = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent)]
            for future in concurrent.futures.as_completed(futures):
                elapsed, success = future.result()
                times.append(elapsed)
                if not success:
                    errors += 1
        total_elapsed = (time.time() - start_all) * 1000

        stats = self._calculate_stats(times, errors, concurrent)
        stats["total_time"] = total_elapsed
        stats["throughput"] = (concurrent / total_elapsed) * 1000  # req/sec
        return stats

    def _generate_csv(self, points: int) -> BytesIO:
        """Generate CSV data"""
        lines = ["x,y,z,temperature,pressure"]
        for i in range(points):
            lines.append(f"{i},{i},{i},{300+i},{101325}")
        return BytesIO("\n".join(lines).encode("utf-8"))

    def _calculate_stats(
        self, times: List[float], errors: int, total: int, extra: Dict = None
    ) -> Dict[str, Any]:
        """Calculate statistics"""
        if not times:
            return {"error": "No data"}

        stats = {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "p95": self._percentile(times, 95),
            "p99": self._percentile(times, 99),
            "errors": errors,
            "error_rate": (errors / total) * 100,
            "total": total,
        }

        if extra:
            stats.update(extra)

        return stats

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _print_stats(self, stats: Dict[str, Any]):
        """Print statistics"""
        if "error" in stats:
            print(f"  Error: {stats['error']}")
            return

        print(f"  Requests: {stats['total']}")
        print(f"  Errors: {stats['errors']} ({stats['error_rate']:.1f}%)")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        print(f"  Mean: {stats['mean']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  StdDev: {stats['stdev']:.2f}ms")
        print(f"  P95: {stats['p95']:.2f}ms")
        print(f"  P99: {stats['p99']:.2f}ms")

        if "throughput" in stats:
            print(f"  Throughput: {stats['throughput']:.2f} req/s")

        if "points" in stats:
            print(f"  Data Points: {stats['points']}")

    def _print_summary(self):
        """Print summary of all benchmarks"""
        for name, result in self.results.items():
            if "error" in result:
                print(f"❌ {name}: {result['error']}")
            elif "mean" in result:
                status = "✅" if result["error_rate"] < 1 else "⚠️"
                print(f"{status} {name}: {result['mean']:.2f}ms (±{result['stdev']:.2f}ms)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run performance benchmarks")
    parser.add_argument("--host", default="http://localhost:8000", help="API host URL")
    args = parser.parse_args()

    benchmark = PerformanceBenchmark(base_url=args.host)
    benchmark.run_all_benchmarks()
