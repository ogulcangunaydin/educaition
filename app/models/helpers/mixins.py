from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr

class SoftDeleteMixin:
    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True)

    def delete(self):
        self.deleted_at = func.now()
        self.save()

    def undelete(self):
        self.deleted_at = None
        self.save()
