from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import Text, String, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Trace(Base):
    __tablename__ = "traces"

    # Removed trailing commas and fixed types
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retrieved_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )


class Verdict(Base):
    __tablename__ = "verdicts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Corrected ForeignKey syntax to reference the 'traces.id' column
    trace_id: Mapped[int] = mapped_column(ForeignKey("traces.id"), nullable=False)
    
    actual_response: Mapped[str] = mapped_column(Text, nullable=False)
    expected_response: Mapped[str] = mapped_column(Text, nullable=False)
    retrieval_relevant: Mapped[bool] = mapped_column(nullable=False)
    faithful: Mapped[bool] = mapped_column(nullable=False)
    correct: Mapped[bool] = mapped_column(nullable=False)
    primary_failure_mode: Mapped[str] = mapped_column(String, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )

class SafetyVerdictRecord(Base):
    __tablename__ = "safety_verdicts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("traces.id"), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    attack_type: Mapped[str] = mapped_column(String, nullable=False)
    actual_response: Mapped[str] = mapped_column(Text, nullable=False)
    expected_safe_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    stayed_in_scope: Mapped[bool] = mapped_column(nullable=False)
    resisted_manipulation: Mapped[bool] = mapped_column(nullable=False)
    leaked_instructions: Mapped[bool] = mapped_column(nullable=False)
    passed: Mapped[bool] = mapped_column(nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )