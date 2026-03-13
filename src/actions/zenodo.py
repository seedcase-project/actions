from pathlib import Path
from typing import Optional

import requests
from pydantic import BaseModel, ConfigDict

from actions.internals import _filter, _map


class ZenodoModel(BaseModel):
    """Model configuring all Zenodo models."""

    model_config = ConfigDict(extra="allow", frozen=True)


class ZenodoCreator(ZenodoModel):
    """Model representing the creator of a Zenodo record.

    Attributes:
        name: The name of the creator.
        affiliation: The affiliation of the creator.
        orcid: The ORCID of the creator.
    """

    name: str
    affiliation: str
    orcid: str


class ZenodoRelatedIdentifier(ZenodoModel):
    """Model representing an identifier related to a Zenodo record.

    Attributes:
        identifier: The value of the identifier.
        relation: The relationship between the record and the other piece of work
            identified by the identifier.
        resource_type: The type of the work identified by the identifier.
        scheme: The scheme followed by the identifier.
    """

    identifier: str
    relation: str
    resource_type: str
    scheme: Optional[str] = None


class ZenodoMetadata(ZenodoModel):
    """Model representing Zenodo metadata.

    Attributes:
        title: The title of the record.
        upload_type: The type of the record.
        creators: The creators of the record.
        related_identifiers: Identifiers related to the record.
    """

    title: str
    upload_type: str
    creators: list[ZenodoCreator]
    related_identifiers: list[ZenodoRelatedIdentifier] = []


class ZenodoLinks(ZenodoModel):
    """Model representing the group of links in Zenodo metadata.

    Attributes:
        bucket: The file upload link for the record.
    """

    # Published records cannot receive new file uploads
    bucket: Optional[str] = None


class ZenodoRecord(ZenodoModel):
    """Model representing a Zenodo record.

    Attributes:
        id: The ID of the record.
        metadata: The metadata the record.
        links: Links to record assets and API endpoints.
    """

    id: int
    metadata: ZenodoMetadata
    links: ZenodoLinks


def zenodo_get_record(token: str) -> Optional[ZenodoRecord]:
    """Gets the Zenodo record for the repository if it exists.

    Args:
        token: Zenodo API access token.

    Returns:
        The Zenodo record for the repo if it exists, None otherwise.
    """
    repo_url = _get_repo_url()

    response = requests.get(
        "https://zenodo.org/api/deposit/depositions",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    response.raise_for_status()
    records: list[ZenodoRecord] = _map(response.json(), ZenodoRecord.model_validate)
    matching_records = _filter(
        records,
        lambda record: bool(
            _filter(
                record.metadata.related_identifiers,
                lambda id: id.relation == "isIdenticalTo" and id.identifier == repo_url,
            )
        ),
    )

    if len(matching_records) > 1:
        raise ValueError(
            "Cannot identify Zenodo record because multiple records exist on Zenodo "
            f"with {repo_url!r} as a related identifier."
        )
    if not matching_records:
        return None
    return matching_records[0]


def zenodo_create_record(token: str) -> None:
    """Create a new Zenodo concept record and publish the first version.

    Args:
        token: Zenodo API access token.
    """
    ...


def zenodo_update_record(token: str, id: int) -> None:
    """Publish a new version of an existing Zenodo concept record.

    Args:
        token: Zenodo API access token.
        id: Zenodo record ID.
    """
    ...


def _load_zenodo_json() -> ZenodoMetadata:
    return ZenodoMetadata.model_validate_json(Path(".zenodo.json").read_text())


def _get_repo_url() -> str:
    metadata = _load_zenodo_json()
    ids = _filter(
        metadata.related_identifiers,
        lambda id: id.relation == "isIdenticalTo" and id.scheme == "url",
    )
    if len(ids) != 1:
        raise ValueError(
            "Expected 1 URL-type related identifier in `.zenodo.json` "
            f"but found {len(ids)}."
        )

    return ids[0].identifier
