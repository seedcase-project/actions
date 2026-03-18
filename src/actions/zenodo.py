from pathlib import Path
from typing import Literal, Optional, Union

import requests
from pydantic import BaseModel, ConfigDict, TypeAdapter

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
        latest_draft: Link to the latest draft or the record.
    """

    # Published records cannot receive new file uploads
    bucket: Optional[str] = None
    latest_draft: str


class ZenodoFile(ZenodoModel):
    """Model representing a file on a Zenodo record."""


type ZenodoRecordState = Literal["done", "inprogress", "error", "unsubmitted"]


class ZenodoRecord(ZenodoModel):
    """Model representing a Zenodo record.

    Attributes:
        id: The ID of the record.
        metadata: The metadata the record.
        links: Links to record assets and API endpoints.
        state: The state of the record.
        submitted: Whether the record has been published.
    """

    id: int
    metadata: ZenodoMetadata
    links: ZenodoLinks
    state: ZenodoRecordState
    submitted: bool

    @property
    def editable(self) -> bool:
        """Whether the record can be edited."""
        return self.state in ["inprogress", "unsubmitted"]


def zenodo_get_record(token: str) -> Optional[ZenodoRecord]:
    """Gets the Zenodo record for the repository if it exists.

    Gets the repository URL from the `.zenodo.json` file. If one
    doesn't exist, this function will not work.

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
                lambda id: id.relation == "IsDerivedFrom" and id.identifier == repo_url,
            )
        ),
    )

    if len(matching_records) > 1:
        raise ValueError(
            "There are multiple records on Zenodo with the repository URL"
            f"{repo_url!r} as a 'related identifier'. We only allow one."
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
        lambda id: id.relation == "IsDerivedFrom",
    )
    if len(ids) != 1:
        raise ValueError(
            "Expected one (1) `IsDerivedFrom` related identifier in `.zenodo.json` "
            f"but found {len(ids)}. The identifier is used to find the matching "
            "Zenodo record and should contain the repository URL."
        )

    return ids[0].identifier


class ZenodoClient:
    """Class for interacting with the Zenodo API."""

    def __init__(self, sandbox: bool, token: str, timeout: int = 30):
        """Initialises the client.

        Args:
            sandbox: Whether to use the sandbox API or the real one.
            token: Zenodo access token.
            timeout: Request timeout in seconds.
        """
        self.headers = {"Authorization": f"Bearer {token}"}
        self.timeout = timeout

        host = "sandbox.zenodo" if sandbox else "zenodo"
        self.depositions = f"https://{host}.org/api/deposit/depositions"

    def _resolve[ResponseType](
        self,
        response: requests.Response,
        response_type: Union[type[ResponseType], list[type[ResponseType]]],
    ) -> ResponseType:
        """Maps the API response to the given model."""
        # TODO: include response.text in error because that is where Zenodo
        # gives reasons
        response.raise_for_status()
        adapter: TypeAdapter[ResponseType] = TypeAdapter(response_type)
        return adapter.validate_python(response.json())

    def get_records(self) -> list[ZenodoRecord]:
        """Gets all records.

        Returns:
            The list of all records.
        """
        response = requests.get(
            self.depositions, headers=self.headers, timeout=self.timeout
        )
        return self._resolve(response, list[ZenodoRecord])

    def get_record(self, record_id: Union[int, str]) -> ZenodoRecord:
        """Gets the record with the given ID.

        Args:
            record_id: The ID of the record.

        Returns:
            The record.

        Raises:
            requests.exceptions.HTTPError: If there is no record with the given ID.
        """
        response = requests.get(
            f"{self.depositions}/{record_id}",
            headers=self.headers,
            timeout=self.timeout,
        )
        return self._resolve(response, ZenodoRecord)

    def upload_file(self, record: ZenodoRecord, file_path: Path) -> ZenodoFile:
        """Uploads a file to a record. The record must be unpublished.

        Args:
            record: The record.
            file_path: The path to the file.

        Returns:
            The updated record.
        """
        if record.submitted:
            raise ValueError(
                f"Cannot upload new file to record {record.id} because the record "
                "has already been published. You must first create a new version "
                "of the record and upload the files there."
            )

        if not record.links.bucket:
            raise ValueError(
                f"Cannot upload new file to record {record.id} because the record "
                "does not have a file-upload (bucket) link. "
            )

        with file_path.open("rb") as file_stream:
            response = requests.put(
                f"{record.links.bucket}/{file_path.name}",
                data=file_stream,
                headers=self.headers,
                timeout=self.timeout,
            )
        return self._resolve(response, ZenodoFile)
