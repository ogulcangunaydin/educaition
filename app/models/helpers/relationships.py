from sqlalchemy.orm import relationship

def has_many(target, **kwargs):
    return relationship(target, **kwargs)

def has_one(target, **kwargs):
    return relationship(target, uselist=False, **kwargs)

def belongs_to(target, **kwargs):
    return relationship(target, **kwargs)
