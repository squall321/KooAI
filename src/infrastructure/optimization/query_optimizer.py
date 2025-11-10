"""
Database query optimization utilities
"""

import functools
from typing import Any, Callable, List, Optional, Sequence, Iterator
from contextlib import contextmanager
import structlog

logger = structlog.get_logger(__name__)


class QueryOptimizer:
    """
    Query optimization utilities

    Provides tools for optimizing database queries:
    - Batch processing
    - Query planning hints
    - Index recommendations
    """

    @staticmethod
    def batch_process(
        items: Sequence[Any],
        processor: Callable,
        batch_size: int = 100,
    ) -> List[Any]:
        """
        Process items in batches

        Args:
            items: Items to process
            processor: Function to process each batch
            batch_size: Batch size

        Returns:
            List of results
        """
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)

        return results

    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
        """
        Split list into chunks

        Args:
            items: List to split
            chunk_size: Size of each chunk

        Returns:
            List of chunks
        """
        return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    @contextmanager
    def bulk_insert_context(session: Any) -> Iterator[Any]:
        """
        Context manager for bulk inserts with optimizations

        Args:
            session: Database session

        Example:
            with QueryOptimizer.bulk_insert_context(session):
                for item in items:
                    session.add(item)
        """
        # Disable autoflush for bulk operations
        autoflush = session.autoflush
        session.autoflush = False

        try:
            yield session
            session.flush()
        finally:
            session.autoflush = autoflush

    @staticmethod
    def explain_query(session: Any, query: Any) -> dict:
        """
        Get query execution plan

        Args:
            session: Database session
            query: SQLAlchemy query

        Returns:
            Query plan information
        """
        try:
            # For PostgreSQL
            explain_query = session.execute(f"EXPLAIN ANALYZE {query}")
            plan = [row for row in explain_query]

            return {
                "plan": plan,
                "query": str(query),
            }
        except Exception as e:
            logger.warning("explain_query_failed", error=str(e))
            return {
                "error": str(e),
                "query": str(query),
            }


def optimize_query(
    fetch_related: Optional[List[str]] = None,
    use_cache: bool = True,
    batch_size: Optional[int] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to optimize database queries

    Args:
        fetch_related: List of relationships to eager load
        use_cache: Whether to use query result caching
        batch_size: Batch size for processing

    Example:
        @optimize_query(fetch_related=["user", "comments"])
        def get_posts(limit: int):
            return session.query(Post).limit(limit).all()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.debug(
                "optimizing_query",
                function=func.__name__,
                fetch_related=fetch_related,
                use_cache=use_cache,
            )

            result = func(*args, **kwargs)

            # Additional optimizations can be added here
            # e.g., result prefetching, caching, etc.

            return result

        return wrapper

    return decorator


def batch_query(batch_size: int = 100, key_param: str = "ids") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to batch query operations

    Args:
        batch_size: Size of each batch
        key_param: Name of the parameter containing IDs to batch

    Example:
        @batch_query(batch_size=100, key_param="user_ids")
        def get_users(user_ids: List[int]):
            return session.query(User).filter(User.id.in_(user_ids)).all()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract IDs from kwargs
            ids = kwargs.get(key_param)

            if ids is None or len(ids) <= batch_size:
                # No batching needed
                return func(*args, **kwargs)

            # Process in batches
            optimizer = QueryOptimizer()
            chunks = optimizer.chunk_list(list(ids), batch_size)

            all_results = []
            for chunk in chunks:
                kwargs[key_param] = chunk
                results = func(*args, **kwargs)
                all_results.extend(results)

            return all_results

        return wrapper

    return decorator


class ConnectionPoolManager:
    """
    Database connection pool manager

    Provides utilities for managing connection pools.
    """

    @staticmethod
    def get_pool_stats(engine: Any) -> dict:
        """
        Get connection pool statistics

        Args:
            engine: SQLAlchemy engine

        Returns:
            Pool statistics
        """
        pool = engine.pool

        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow(),
        }

    @staticmethod
    def configure_pool(
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
    ) -> dict:
        """
        Get optimized pool configuration

        Args:
            pool_size: Base pool size
            max_overflow: Maximum overflow connections
            pool_timeout: Connection timeout
            pool_recycle: Connection recycle time
            pool_pre_ping: Enable connection health check

        Returns:
            Pool configuration dictionary
        """
        return {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle,
            "pool_pre_ping": pool_pre_ping,
        }


class IndexManager:
    """
    Database index management utilities
    """

    @staticmethod
    def suggest_indexes(session: Any, table_name: str) -> List[dict]:
        """
        Suggest indexes for a table based on query patterns

        Args:
            session: Database session
            table_name: Table name

        Returns:
            List of index suggestions
        """
        # This is a placeholder - real implementation would analyze
        # query patterns and suggest appropriate indexes

        suggestions = []

        # Example suggestions
        suggestions.append(
            {
                "table": table_name,
                "columns": ["created_at"],
                "reason": "Frequently used in WHERE clauses for time-based queries",
            }
        )

        return suggestions

    @staticmethod
    def create_index_sql(
        table_name: str,
        columns: List[str],
        index_name: Optional[str] = None,
        unique: bool = False,
    ) -> str:
        """
        Generate CREATE INDEX SQL

        Args:
            table_name: Table name
            columns: Columns to index
            index_name: Custom index name
            unique: Create unique index

        Returns:
            SQL statement
        """
        if index_name is None:
            index_name = f"idx_{'_'.join(columns)}"

        unique_keyword = "UNIQUE " if unique else ""
        columns_str = ", ".join(columns)

        return f"CREATE {unique_keyword}INDEX {index_name} ON {table_name} ({columns_str});"
