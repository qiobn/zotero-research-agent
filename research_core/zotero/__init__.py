"""Zotero API wrappers — pyzotero facade, Item/Attachment/Annotation models."""

from research_core.zotero.client import ZoteroClient
from research_core.zotero.models import Annotation, Attachment, Item

__all__ = ["ZoteroClient", "Item", "Attachment", "Annotation"]
