import json
from pathlib import Path
from typing import Any, Optional, cast

from zen import Zenodo
from zen.dataset import Deposition

from actions.internals import _filter


def zenodo_get_record(zen: Zenodo) -> Optional[Deposition]:
    """Gets the Zenodo record for the repository if it exists.

    Args:
        zen: Zenodo client.

    Returns:
        The Zenodo record for the repo if it exists, None otherwise.
    """
    repo_url = _get_repo_url()
    # Fetch all user records from Zenodo
    records: list[Deposition] = zen.depositions.list()

    matching_records = _filter(
        records,
        lambda record: bool(
            _filter(
                record.metadata.related_identifiers.data,
                lambda id: (
                    id["relation"] == "isIdenticalTo" and id["identifier"] == repo_url
                ),
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


def zenodo_create_record(zen: Zenodo) -> None:
    """Create a new Zenodo concept record and publish the first version.

    Args:
        zen: Zenodo client.
    """
    metadata = _load_zenodo_json()
    # Create new record with metadata
    new_record = zen.depositions.create(metadata=metadata)
    # Upload file
    zen.api.create_deposition_file(new_record.id, "book.pdf", "book.pdf")
    # Publish record
    new_record.publish()


def zenodo_update_record(record: Deposition) -> None:
    """Publish a new version of an existing Zenodo concept record.

    Args:
        zen: Zenodo client.
        record: The existing Zenodo record.
    """
    # If the record is being edited, discard draft
    if record.is_editing:
        record.discard()
    # Create a new record
    new_record = record.new_version()
    # Put new record in edit mode
    new_record.edit()
    # Update file
    new_record.api.api.create_deposition_file(new_record.id, "book.pdf", "book.pdf")
    # Update metadata
    metadata = _load_zenodo_json()
    new_record.update(metadata=metadata)
    # Publish record
    new_record.publish()


def _load_zenodo_json() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(Path(".zenodo.json").read_text()))


def _get_repo_url() -> str:
    metadata = _load_zenodo_json()
    ids = _filter(
        metadata["related_identifiers"],
        lambda id: id["relation"] == "isIdenticalTo" and id["scheme"] == "url",
    )
    if len(ids) != 1:
        raise ValueError(
            "Expected 1 URL-type related identifier in `.zenodo.json` "
            f"but found {len(ids)}."
        )

    return cast(str, ids[0]["identifier"])
