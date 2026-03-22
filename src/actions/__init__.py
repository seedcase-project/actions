"""Module containing all source code."""

from .cli import zenodo_publish
from .examples import example_metadata, example_record
from .zenodo import (
    ZenodoClient,
    ZenodoCreator,
    ZenodoLinks,
    ZenodoMetadata,
    ZenodoRecord,
    ZenodoRecordState,
    ZenodoRelatedIdentifier,
)

__all__ = [
    "example_metadata",
    "example_record",
    "zenodo_publish",
    "ZenodoClient",
    "ZenodoCreator",
    "ZenodoLinks",
    "ZenodoMetadata",
    "ZenodoRecord",
    "ZenodoRecordState",
    "ZenodoRelatedIdentifier",
]
