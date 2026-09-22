from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.base import Base

class UserRecord(Base):

    __tablename__ = "user_records"

    id           = Column(Integer, primary_key=True, index=True, autoincrement=True)

    user_id      = Column(String(64), unique=True, nullable=False, index=True)

    email        = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(256), nullable=True)
    name         = Column(String(255), nullable=True)
    is_active    = Column(Boolean, default=True, nullable=False)

    profile_json = Column(JSON, nullable=True,
                          comment="Serialised UserProfile (biometrics, goals, etc.)")

    analysis_consent = Column(Boolean, default=False, nullable=False)

    created_at   = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at   = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    plans = relationship(
        "FitnessPlanRecord",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<UserRecord id={self.id} user_id={self.user_id!r} email={self.email!r}>"


class FitnessPlanRecord(Base):

    __tablename__ = "fitness_plan_records"

    id           = Column(Integer, primary_key=True, index=True, autoincrement=True)

    job_id       = Column(String(64), unique=True, nullable=False, index=True)

    user_id      = Column(
        String(64),
        ForeignKey("user_records.user_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    status       = Column(String(16), default="pending", nullable=False, index=True)

    request_json = Column(JSON, nullable=True,
                          comment="Serialised GeneratePlanRequest sent by the client")

    plan_json    = Column(JSON, nullable=True,
                          comment="Serialised FitnessPlan — populated when status=done")

    error_detail = Column(Text, nullable=True)

    youtube_urls = Column(JSON, nullable=True,
                          comment="List of YouTube URLs used to generate this plan")

    created_at   = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("UserRecord", back_populates="plans")

    def __repr__(self) -> str:
        return (
            f"<FitnessPlanRecord id={self.id} job_id={self.job_id!r} "
            f"status={self.status!r} user_id={self.user_id!r}>"
        )


UserProfileModel = UserRecord
