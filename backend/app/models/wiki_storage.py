import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Integer, Boolean, Table, Column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dal import Base


wiki_page_tags = Table(
    "wiki_page_tags",
    Base.metadata,
    Column("page_id", UUID(as_uuid=True), ForeignKey("wiki_pages.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("wiki_tags.id", ondelete="CASCADE"), primary_key=True),
)


class WikiFile(Base):
    __tablename__ = "wiki_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wiki_pages.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    md5_hash: Mapped[str] = mapped_column(String(32), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="text/markdown")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    edit_summary: Mapped[str | None] = mapped_column(String(500))

    page: Mapped["WikiPage"] = relationship("WikiPage", back_populates="files")
    chunks: Mapped[list["WikiChunk"]] = relationship("WikiChunk", back_populates="file", cascade="all, delete-orphan")


class WikiChunk(Base):
    __tablename__ = "wiki_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wiki_files.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_pos: Mapped[int] = mapped_column(Integer, nullable=False)
    end_pos: Mapped[int] = mapped_column(Integer, nullable=False)
    text_preview: Mapped[str] = mapped_column(String(200))
    vector_id: Mapped[str] = mapped_column(String(100), nullable=False)

    file: Mapped["WikiFile"] = relationship("WikiFile", back_populates="chunks")


class WikiTag(Base):
    __tablename__ = "wiki_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#3B82F6")
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wiki_tags.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    parent: Mapped["WikiTag | None"] = relationship("WikiTag", remote_side=[id])
    pages: Mapped[list["WikiPage"]] = relationship("WikiPage", secondary=wiki_page_tags, back_populates="tags")


class ChunkingRule(Base):
    __tablename__ = "chunking_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
