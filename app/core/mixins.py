"""
Reusable SQLAlchemy mixins for common model patterns.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql import func


# Define which relationships should cascade soft delete
# Format: {parent_table: [(relationship_name, child_has_soft_delete), ...]}
SOFT_DELETE_CASCADE_RELATIONSHIPS = {
    "rooms": [("players", True), ("sessions", True)],
    "high_school_rooms": [("students", True)],
    "users": [("rooms", True), ("dissonance_test_participants", True), ("high_school_rooms", True)],
}


class SoftDeleteMixin:
    """
    Mixin that adds soft delete functionality to models.
    
    Instead of permanently deleting records, sets a `deleted_at` timestamp.
    Records with `deleted_at` set are considered "deleted" and should be
    filtered out in normal queries.
    
    Cascade Behavior:
        Define cascading relationships in SOFT_DELETE_CASCADE_RELATIONSHIPS.
        When soft_delete(cascade=True) is called, it will also soft-delete
        all related records defined in the cascade config.
    
    Usage:
        class User(Base, SoftDeleteMixin):
            __tablename__ = "users"
            # ... other columns
    
    Methods:
        soft_delete(cascade=True): Mark record as deleted, cascade to children
        restore(): Restore a soft-deleted record
        is_deleted: Property to check if record is deleted
    
    Querying:
        Deleted records are automatically filtered out by default.
        Use .execution_options(include_deleted=True) to include deleted records.
    """
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
        doc="Timestamp when the record was soft-deleted. NULL means not deleted."
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if the record has been soft-deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self, cascade: bool = True) -> None:
        """
        Mark this record as deleted by setting deleted_at to current time.
        
        Args:
            cascade: If True, also soft-delete related records defined in
                    SOFT_DELETE_CASCADE_RELATIONSHIPS.
        """
        if cascade:
            self._cascade_soft_delete()
        self.deleted_at = datetime.now()
    
    def _cascade_soft_delete(self) -> None:
        """Cascade soft delete to related records."""
        table_name = getattr(self, "__tablename__", None)
        if not table_name:
            return
        
        cascade_rels = SOFT_DELETE_CASCADE_RELATIONSHIPS.get(table_name, [])
        for rel_name, has_soft_delete in cascade_rels:
            if not has_soft_delete:
                continue
            
            related = getattr(self, rel_name, None)
            if related is None:
                continue
            
            # Handle both single objects and collections
            if hasattr(related, "__iter__"):
                for child in related:
                    if hasattr(child, "soft_delete") and not child.is_deleted:
                        child.soft_delete(cascade=True)
            elif hasattr(related, "soft_delete") and not related.is_deleted:
                related.soft_delete(cascade=True)
    
    def restore(self) -> None:
        """Restore a soft-deleted record by clearing deleted_at."""
        self.deleted_at = None


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps.
    
    Note: Most models already have these columns defined individually.
    This mixin is for new models or refactoring existing ones.
    """
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created."
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        doc="Timestamp when the record was last updated."
    )
