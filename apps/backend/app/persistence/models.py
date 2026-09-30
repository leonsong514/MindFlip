"""SQLAlchemy declarative base and the iteration 01 storage probe table.

The `storage_probe` table is a technical fixture used to verify the
persistence contract (migration, insert, close, reopen, rollback). It
is not a domain entity and will be removed once a real table replaces
it in a later iteration.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class StorageProbe(Base):
    """Technical table used to verify the persistence contract.

    Kept intentionally minimal: a single string value keyed by id.
    """

    __tablename__ = "storage_probe"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
