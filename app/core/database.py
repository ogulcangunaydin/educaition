from collections.abc import Generator
from typing import Any
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, Query
from sqlalchemy.orm.util import AliasedClass
from .config import settings

DATABASE_URL = settings.DATABASE_URL or "postgresql://ogi:hebele@localhost/educaition"
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,  # Enable connection health checks
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Automatically filter out soft-deleted records
@event.listens_for(Query, "before_compile", retval=True)
def auto_filter_soft_deleted(query):
    """
    Automatically adds deleted_at IS NULL filter to queries for models with SoftDeleteMixin.
    
    To include deleted records, use:
        db.query(Model).execution_options(include_deleted=True)
    """
    # Check if we should include deleted records
    if query._execution_options.get("include_deleted", False):
        return query
    
    # Get all entities being queried
    for desc in query.column_descriptions:
        entity = desc.get("entity")
        if entity is None:
            continue
            
        # Handle aliased classes
        if isinstance(entity, AliasedClass):
            mapper_class = entity._aliased_insp.mapper.class_
        else:
            mapper_class = entity
            
        # Check if model has deleted_at column (SoftDeleteMixin)
        if hasattr(mapper_class, "deleted_at"):
            query = query.filter(entity.deleted_at.is_(None))
    
    return query


def get_db() -> Generator[Session, Any, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
