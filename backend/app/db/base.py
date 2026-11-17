from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


def enum_column(enum_cls: type[StrEnum], **kwargs):
    return mapped_column(
        SAEnum(
            enum_cls,
            native_enum=False,
            length=20,
            values_callable=lambda e: [member.value for member in e],
        ),
        **kwargs,
    )
