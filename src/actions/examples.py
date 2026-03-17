from typing import Optional

from .zenodo import (
    ZenodoCreator,
    ZenodoLinks,
    ZenodoMetadata,
    ZenodoRecord,
    ZenodoRecordState,
    ZenodoRelatedIdentifier,
)


def example_metadata(title: str = "Test Poster") -> ZenodoMetadata:
    """A set of example Zenodo metadata."""
    return ZenodoMetadata(
        title=title,
        upload_type="poster",
        creators=[
            ZenodoCreator(
                name="Doe, Jane", affiliation="University of Testfalia", orcid="ABC"
            )
        ],
        related_identifiers=[
            ZenodoRelatedIdentifier(
                identifier="https://github.com/test-repo",
                relation="IsDerivedFrom",
                resource_type="other",
            )
        ],
    )


def example_record(
    id: int = 123,
    metadata: ZenodoMetadata = example_metadata(),
    state: ZenodoRecordState = "done",
    submitted: bool = True,
    bucket: Optional[str] = "https://path.com/path/wrwee-324-23f-sdf",
    repo_url: str = "https://github.com/test-repo",
) -> ZenodoRecord:
    """An example Zenodo record."""
    metadata = metadata.model_copy(
        update={
            "related_identifiers": [
                ZenodoRelatedIdentifier(
                    identifier=repo_url,
                    relation="IsDerivedFrom",
                    resource_type="other",
                )
            ]
        }
    )
    return ZenodoRecord(
        id=id,
        metadata=metadata,
        state=state,
        submitted=submitted,
        links=ZenodoLinks(latest_draft="https://path.com/path/9999", bucket=bucket),
    )
