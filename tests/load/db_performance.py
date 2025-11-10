"""
Database performance testing

Test database query performance, bulk operations, and connection pooling
"""

import time
import statistics
from typing import List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database.models import Base, SimulationModel
from datetime import datetime
import numpy as np


class DatabasePerformanceTest:
    """Database performance testing"""

    def __init__(self, db_url: str = "sqlite:///./test_performance.db") -> None:
        self.db_url = db_url
        self.engine = create_engine(
            db_url,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def run_all_tests(self) -> None:
        """Run all database performance tests"""
        print("=" * 60)
        print("DATABASE PERFORMANCE TESTS")
        print("=" * 60)
        print()

        tests = [
            ("Single Insert", self.test_single_insert),
            ("Bulk Insert (100)", lambda: self.test_bulk_insert(100)),
            ("Bulk Insert (1000)", lambda: self.test_bulk_insert(1000)),
            ("Simple Query", self.test_simple_query),
            ("Complex Query with Filter", self.test_complex_query),
            ("Query with Join", self.test_query_with_join),
            ("Update Performance", self.test_update_performance),
            ("Delete Performance", self.test_delete_performance),
            ("Connection Pool Test", self.test_connection_pool),
            ("Transaction Rollback", self.test_transaction_rollback),
        ]

        for name, test_func in tests:
            print(f"\n{name}:")
            print("-" * 60)
            try:
                result = test_func()  # type: ignore[operator]
                self._print_result(result)
            except Exception as e:
                print(f"❌ Error: {e}")

        # Cleanup
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_single_insert(self, iterations: int = 100) -> Dict[str, Any]:
        """Test single row insert performance"""
        times = []

        for i in range(iterations):
            session = self.SessionLocal()
            try:
                start = time.time()

                sim = SimulationModel(
                    name=f"Test Sim {i}",
                    file_format="CSV",
                    status="completed",
                    file_path=f"/test/path{i}.csv",
                    created_at=datetime.now(),
                )
                session.add(sim)
                session.commit()

                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            finally:
                session.close()

        return self._calculate_stats(times)

    def test_bulk_insert(self, count: int = 100) -> Dict[str, Any]:
        """Test bulk insert performance"""
        times = []

        for batch in range(5):  # 5 batches
            session = self.SessionLocal()
            try:
                start = time.time()

                simulations = [
                    SimulationModel(
                        name=f"Bulk Sim {batch}_{i}",
                        file_format="CSV",
                        status="completed",
                        file_path=f"/bulk/{batch}/{i}.csv",
                        created_at=datetime.now(),
                    )
                    for i in range(count)
                ]

                session.bulk_save_objects(simulations)
                session.commit()

                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            finally:
                session.close()

        stats = self._calculate_stats(times)
        stats["records_per_batch"] = count
        stats["throughput"] = count / (stats["mean"] / 1000)  # records/sec
        return stats

    def test_simple_query(self, iterations: int = 100) -> Dict[str, Any]:
        """Test simple query performance"""
        # Insert test data
        self._insert_test_data(100)

        times = []
        session = self.SessionLocal()

        try:
            for _ in range(iterations):
                start = time.time()
                results = session.query(SimulationModel).all()
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
        finally:
            session.close()

        return self._calculate_stats(times)

    def test_complex_query(self, iterations: int = 50) -> Dict[str, Any]:
        """Test complex query with filters"""
        self._insert_test_data(500)

        times = []
        session = self.SessionLocal()

        try:
            for i in range(iterations):
                start = time.time()
                results = (
                    session.query(SimulationModel)
                    .filter(SimulationModel.status == "completed", SimulationModel.name.like(f"%{i%10}%"))
                    .order_by(SimulationModel.created_at.desc())
                    .limit(10)
                    .all()
                )
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
        finally:
            session.close()

        return self._calculate_stats(times)

    def test_query_with_join(self, iterations: int = 50) -> Dict[str, Any]:
        """Test query with joins"""
        self._insert_test_data(200)

        times = []
        session = self.SessionLocal()

        try:
            for _ in range(iterations):
                start = time.time()
                # Simulate a join query
                results = session.query(SimulationModel).filter(SimulationModel.status == "completed").all()
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
        finally:
            session.close()

        return self._calculate_stats(times)

    def test_update_performance(self, iterations: int = 50) -> Dict[str, Any]:
        """Test update performance"""
        self._insert_test_data(100)

        times = []

        for i in range(iterations):
            session = self.SessionLocal()
            try:
                start = time.time()

                sim = session.query(SimulationModel).first()
                if sim:
                    sim.name = f"Updated {i}"
                    session.commit()

                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            finally:
                session.close()

        return self._calculate_stats(times)

    def test_delete_performance(self, iterations: int = 50) -> Dict[str, Any]:
        """Test delete performance"""
        times = []

        for i in range(iterations):
            # Insert a record
            session = self.SessionLocal()
            sim = SimulationModel(
                name=f"To Delete {i}",
                file_format="CSV",
                status="completed",
                file_path=f"/delete/{i}.csv",
                created_at=datetime.now(),
            )
            session.add(sim)
            session.commit()
            sim_id = sim.id
            session.close()

            # Delete it
            session = self.SessionLocal()
            try:
                start = time.time()

                sim = session.query(SimulationModel).filter(SimulationModel.id == sim_id).first()
                if sim:
                    session.delete(sim)
                    session.commit()

                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            finally:
                session.close()

        return self._calculate_stats(times)

    def test_connection_pool(self, num_concurrent: int = 20) -> Dict[str, Any]:
        """Test connection pool performance"""
        import concurrent.futures

        def make_query() -> float:
            start = time.time()
            session = self.SessionLocal()
            try:
                session.query(SimulationModel).limit(10).all()
                elapsed = (time.time() - start) * 1000
                return elapsed
            finally:
                session.close()

        self._insert_test_data(100)

        times = []
        start_all = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_query) for _ in range(num_concurrent)]
            for future in concurrent.futures.as_completed(futures):
                times.append(future.result())

        total_time = (time.time() - start_all) * 1000

        stats = self._calculate_stats(times)
        stats["total_time"] = total_time
        stats["concurrent_connections"] = num_concurrent
        return stats

    def test_transaction_rollback(self, iterations: int = 50) -> Dict[str, Any]:
        """Test transaction rollback performance"""
        times = []

        for i in range(iterations):
            session = self.SessionLocal()
            try:
                start = time.time()

                # Insert and rollback
                sim = SimulationModel(
                    name=f"Rollback {i}",
                    file_format="CSV",
                    status="completed",
                    file_path=f"/rollback/{i}.csv",
                    created_at=datetime.now(),
                )
                session.add(sim)
                session.flush()  # Flush but don't commit
                session.rollback()  # Rollback

                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            finally:
                session.close()

        return self._calculate_stats(times)

    def _insert_test_data(self, count: int) -> None:
        """Insert test data"""
        session = self.SessionLocal()
        try:
            # Check if already has data
            existing = session.query(SimulationModel).count()
            if existing >= count:
                return

            simulations = [
                SimulationModel(
                    name=f"Test Data {i}",
                    file_format="CSV",
                    status="completed",
                    file_path=f"/test/data{i}.csv",
                    created_at=datetime.now(),
                )
                for i in range(count)
            ]
            session.bulk_save_objects(simulations)
            session.commit()
        finally:
            session.close()

    def _calculate_stats(self, times: List[float]) -> Dict[str, Any]:
        """Calculate statistics"""
        if not times:
            return {}

        return {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "p95": self._percentile(times, 95),
            "p99": self._percentile(times, 99),
            "total": len(times),
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _print_result(self, result: Dict[str, Any]) -> None:
        """Print test result"""
        if not result:
            print("  No data")
            return

        print(f"  Iterations: {result['total']}")
        print(f"  Min: {result['min']:.2f}ms")
        print(f"  Max: {result['max']:.2f}ms")
        print(f"  Mean: {result['mean']:.2f}ms")
        print(f"  Median: {result['median']:.2f}ms")
        print(f"  StdDev: {result['stdev']:.2f}ms")
        print(f"  P95: {result['p95']:.2f}ms")
        print(f"  P99: {result['p99']:.2f}ms")

        if "throughput" in result:
            print(f"  Throughput: {result['throughput']:.2f} records/sec")

        if "concurrent_connections" in result:
            print(f"  Concurrent: {result['concurrent_connections']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run database performance tests")
    parser.add_argument("--db-url", default="sqlite:///./test_performance.db", help="Database URL")
    args = parser.parse_args()

    tester = DatabasePerformanceTest(db_url=args.db_url)
    tester.run_all_tests()
