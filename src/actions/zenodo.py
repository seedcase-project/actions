from pathlib import Path
from typing import Literal, Optional, TypeVar, Union

import requests
from pydantic import BaseModel, ConfigDict, TypeAdapter

from actions.internals import _filter


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
    orcid: str
    affiliation: str


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


def zenodo_find_record_by_repo_url(
    records: list[ZenodoRecord],
) -> Optional[ZenodoRecord]:
    """Gets the Zenodo record for the repository if it exists.

    Gets the repository URL from the `.zenodo.json` file. If one
    doesn't exist, this function will not work.

    Args:
        records: All Zenodo records for the user.

    Returns:
        The Zenodo record for the repo if it exists, None otherwise.
    """
    repo_url = _get_repo_url()
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


def _load_zenodo_json() -> ZenodoMetadata:
    return ZenodoMetadata.model_validate_json(Path(".zenodo.json").read_text())


def _get_repo_url() -> str:
    metadata = _load_zenodo_json()
    ids = _filter(
        metadata.related_identifiers,
        lambda id: id.relation == "IsDerivedFrom" and id.scheme == "url",
    )
    if len(ids) != 1:
        raise ValueError(
            "Expected one (1) `IsDerivedFrom` related identifier in `.zenodo.json` "
            f"but found {len(ids)}. The identifier is used to find the matching "
            "Zenodo record and should contain the repository URL."
        )

    return ids[0].identifier


# Type of response returned by the Zenodo API
ResponseType = TypeVar("ResponseType")


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

    def create_record(self, metadata: ZenodoMetadata) -> ZenodoRecord:
        """Creates a new record in editable state.

        Args:
            metadata: The metadata of the new record.

        Returns:
            The newly created record.
        """
        response = requests.post(
            self.depositions,
            headers=self.headers,
            json={"metadata": metadata.model_dump()},
            timeout=self.timeout,
        )
        return self._resolve(response, ZenodoRecord)

    def update_metadata(
        self, record: ZenodoRecord, metadata: ZenodoMetadata
    ) -> ZenodoRecord:
        """Updates the metadata of a record.

        Args:
            record: The record.
            metadata: The new metadata.

        Returns:
            The updated record.
        """
        record = self.make_editable(record)
        response = requests.put(
            f"{self.depositions}/{record.id}",
            headers=self.headers,
            json={"metadata": metadata.model_dump()},
            timeout=self.timeout,
        )
        return self._resolve(response, ZenodoRecord)

    def make_editable(self, record: ZenodoRecord) -> ZenodoRecord:
        """Makes the record editable.

        Args:
            record: The record.

        Returns:
            The record in editable state.
        """
        if record.editable:
            return record

        response = requests.post(
            f"{self.depositions}/{record.id}/actions/edit",
            headers=self.headers,
            timeout=self.timeout,
        )
        return self._resolve(response, ZenodoRecord)

    def discard_draft(self, record: ZenodoRecord) -> None:
        """Puts the record in a non-editable state by discarding all changes.

        Args:
            record: The record.
        """
        if not record.editable:
            return None

        response = requests.post(
            f"{self.depositions}/{record.id}/actions/discard",
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()

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

    def create_new_version(self, record: ZenodoRecord) -> ZenodoRecord:
        """Creates a new, unpublished version of a published record.

        Args:
            record: The record.

        Returns:
            The new version of the record.
        """
        if not record.submitted:
            raise ValueError(
                f"Cannot create new version for record {record.id} because it "
                "has not yet been published."
            )

        self.discard_draft(record)
        response = requests.post(
            f"{self.depositions}/{record.id}/actions/newversion",
            headers=self.headers,
            timeout=self.timeout,
        )
        record = self._resolve(response, ZenodoRecord)

        new_record_id = Path(record.links.latest_draft).name
        return self.get_record(new_record_id)

    def publish(self, record: ZenodoRecord) -> ZenodoRecord:
        """Publishes a record.

        Args:
            record: The record.

        Returns:
            The published record.
        """
        if record.submitted and record.state == "done":
            return record

        response = requests.post(
            f"{self.depositions}/{record.id}/actions/publish",
            headers=self.headers,
            timeout=self.timeout,
        )
        return self._resolve(response, ZenodoRecord)

    def publish_new_record(
        self, metadata: ZenodoMetadata, file_path: Path
    ) -> ZenodoRecord:
        """Creates and publishes a new record.

        The given file and metadata are uploaded to the new record.

        Args:
            metadata: The metadata.
            file_path: The path to the file to upload.

        Returns:
            The published record.
        """
        record = self.create_record(metadata)
        self.upload_file(record, file_path)
        return self.publish(record)

    def publish_updated_record(
        self, record: ZenodoRecord, metadata: ZenodoMetadata, file_path: Path
    ) -> ZenodoRecord:
        """Updates a published record with the given file and metadata.

        Args:
            record: The record to update.
            metadata: The metadata.
            file_path: The path to the file to upload.

        Returns:
            The published record.
        """
        new_record = self.create_new_version(record)
        self.upload_file(new_record, file_path)
        new_record = self.update_metadata(new_record, metadata)
        return self.publish(new_record)

    def _resolve(
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
