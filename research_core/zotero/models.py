"""Unified data models for Zotero items."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    key: str
    filename: str = ""
    content_type: str = ""
    path: str | None = None


class Annotation(BaseModel):
    key: str
    text: str = ""
    comment: str = ""
    page: int | None = None
    color: str = ""
    annotation_type: str = "highlight"


class Item(BaseModel):
    key: str
    title: str = ""
    abstract: str = ""
    authors: list[str] = Field(default_factory=list)
    date: str = ""
    doi: str = ""
    url: str = ""
    item_type: str = ""
    tags: list[str] = Field(default_factory=list)
    collections: list[str] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    annotations: list[Annotation] = Field(default_factory=list)
    citation_key: str = ""
    version: int = 0
