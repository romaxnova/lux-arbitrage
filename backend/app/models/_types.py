"""Portable column types (SQLite local + PostgreSQL production)."""

import uuid

from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

PkUUID = Uuid(as_uuid=True)
JsonDict = JSON
JsonList = JSON
