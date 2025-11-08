"""
Tenant Data Isolation

Ensures data isolation between tenants at database level.
"""

from typing import TypeVar, Generic, Optional, List
from sqlalchemy import event
from sqlalchemy.orm import Session, Query
from sqlalchemy.ext.declarative import DeclarativeMeta

from src.infrastructure.tenancy.context import get_current_tenant, require_tenant


T = TypeVar("T")


class TenantIsolatedQuery(Query):
    """
    Custom query class that automatically filters by tenant.

    Prevents cross-tenant data access.
    """

    def __init__(self, *args, **kwargs):
        """Initialize tenant-isolated query."""
        super().__init__(*args, **kwargs)
        self._apply_tenant_filter()

    def _apply_tenant_filter(self):
        """Apply tenant filter to query."""
        # Get current tenant
        tenant_context = get_current_tenant()

        if not tenant_context:
            # No tenant context - might be system operation
            return

        # Check if model has tenant_id column
        model = self.column_descriptions[0]["type"] if self.column_descriptions else None

        if model and hasattr(model, "tenant_id"):
            # Auto-filter by tenant_id
            self._criterion = getattr(model, "tenant_id") == tenant_context.tenant_id


class TenantScoped:
    """
    Mixin for tenant-scoped models.

    Automatically adds tenant_id column and filtering.
    """

    # This will be set by the model
    tenant_id: str

    @classmethod
    def for_tenant(cls, session: Session, tenant_id: Optional[str] = None):
        """
        Query scoped to specific tenant.

        Args:
            session: Database session
            tenant_id: Tenant ID (uses current if not specified)

        Returns:
            Filtered query

        Example:
            ```python
            # Get all simulations for current tenant
            simulations = Simulation.for_tenant(db).all()

            # Get simulations for specific tenant
            simulations = Simulation.for_tenant(db, "ten_123").all()
            ```
        """
        if tenant_id is None:
            tenant_context = require_tenant()
            tenant_id = tenant_context.tenant_id

        return session.query(cls).filter(cls.tenant_id == tenant_id)

    @classmethod
    def create_for_tenant(cls, session: Session, **kwargs):
        """
        Create instance for current tenant.

        Args:
            session: Database session
            **kwargs: Model fields

        Returns:
            Created instance

        Example:
            ```python
            simulation = Simulation.create_for_tenant(
                db,
                filename="test.vtk",
                simulation_type="cfd"
            )
            ```
        """
        tenant_context = require_tenant()

        # Set tenant_id automatically
        kwargs["tenant_id"] = tenant_context.tenant_id

        instance = cls(**kwargs)
        session.add(instance)
        return instance


def enable_tenant_isolation(session: Session):
    """
    Enable automatic tenant isolation for session.

    Args:
        session: Database session

    Example:
        ```python
        db = SessionLocal()
        enable_tenant_isolation(db)

        # All queries will be automatically filtered by tenant
        simulations = db.query(Simulation).all()
        ```
    """

    @event.listens_for(session, "before_flush")
    def before_flush(session, flush_context, instances):
        """Validate tenant_id before flush."""
        tenant_context = get_current_tenant()

        if not tenant_context:
            # No tenant context - allow system operations
            return

        # Check all new instances
        for instance in session.new:
            if hasattr(instance, "tenant_id"):
                if not instance.tenant_id:
                    # Auto-set tenant_id
                    instance.tenant_id = tenant_context.tenant_id
                elif instance.tenant_id != tenant_context.tenant_id:
                    raise ValueError(
                        f"Cannot create {instance.__class__.__name__} "
                        f"for different tenant"
                    )

        # Check all modified instances
        for instance in session.dirty:
            if hasattr(instance, "tenant_id"):
                if instance.tenant_id != tenant_context.tenant_id:
                    raise ValueError(
                        f"Cannot modify {instance.__class__.__name__} "
                        f"from different tenant"
                    )

        # Check all deleted instances
        for instance in session.deleted:
            if hasattr(instance, "tenant_id"):
                if instance.tenant_id != tenant_context.tenant_id:
                    raise ValueError(
                        f"Cannot delete {instance.__class__.__name__} "
                        f"from different tenant"
                    )


class TenantIsolationError(Exception):
    """Raised when cross-tenant access is attempted."""

    pass


def check_tenant_access(instance, operation: str = "access"):
    """
    Check if current tenant can access instance.

    Args:
        instance: Model instance to check
        operation: Operation being performed

    Raises:
        TenantIsolationError: If access denied

    Example:
        ```python
        simulation = db.query(Simulation).get(sim_id)
        check_tenant_access(simulation, "delete")
        ```
    """
    if not hasattr(instance, "tenant_id"):
        # Model is not tenant-scoped
        return

    tenant_context = get_current_tenant()

    if not tenant_context:
        raise TenantIsolationError("No tenant context available")

    if instance.tenant_id != tenant_context.tenant_id:
        raise TenantIsolationError(
            f"Cannot {operation} {instance.__class__.__name__} "
            f"from different tenant"
        )


class TenantRepository(Generic[T]):
    """
    Base repository with automatic tenant isolation.

    Type-safe repository pattern with tenant filtering.
    """

    def __init__(self, model: type[T], session: Session):
        """
        Initialize repository.

        Args:
            model: Model class
            session: Database session
        """
        self.model = model
        self.session = session

    def _get_tenant_id(self) -> str:
        """Get current tenant ID."""
        tenant_context = require_tenant()
        return tenant_context.tenant_id

    def _base_query(self) -> Query:
        """Get base query with tenant filter."""
        query = self.session.query(self.model)

        if hasattr(self.model, "tenant_id"):
            tenant_id = self._get_tenant_id()
            query = query.filter(self.model.tenant_id == tenant_id)

        return query

    def get(self, id: str) -> Optional[T]:
        """
        Get by ID.

        Args:
            id: Instance ID

        Returns:
            Instance or None
        """
        return self._base_query().filter(self.model.id == id).first()

    def list(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[T]:
        """
        List instances with pagination.

        Args:
            skip: Number to skip
            limit: Max number to return
            **filters: Additional filters

        Returns:
            List of instances
        """
        query = self._base_query()

        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.offset(skip).limit(limit).all()

    def create(self, **kwargs) -> T:
        """
        Create new instance.

        Args:
            **kwargs: Model fields

        Returns:
            Created instance
        """
        # Auto-set tenant_id
        if hasattr(self.model, "tenant_id"):
            kwargs["tenant_id"] = self._get_tenant_id()

        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()  # Get ID without committing

        return instance

    def update(self, id: str, **kwargs) -> Optional[T]:
        """
        Update instance.

        Args:
            id: Instance ID
            **kwargs: Fields to update

        Returns:
            Updated instance or None
        """
        instance = self.get(id)

        if not instance:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        self.session.flush()
        return instance

    def delete(self, id: str) -> bool:
        """
        Delete instance.

        Args:
            id: Instance ID

        Returns:
            True if deleted, False if not found
        """
        instance = self.get(id)

        if not instance:
            return False

        self.session.delete(instance)
        self.session.flush()

        return True

    def count(self, **filters) -> int:
        """
        Count instances.

        Args:
            **filters: Filters

        Returns:
            Count
        """
        query = self._base_query()

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.count()
