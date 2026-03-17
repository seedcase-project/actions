import os
from pathlib import Path

from cyclopts import App

from actions.zenodo import (
    ZenodoClient,
    _load_zenodo_json,
    zenodo_find_record_by_repo_url,
)

app = App(
    name="actions",
    help=(
        "The `actions` package contains GitHub reusable workflows and "
        "actions used in the Seedcase Project."
    ),
)


# TODO: add sandbox param
@app.command()
def zenodo_publish() -> None:
    """Publish a new version of the repository on Zenodo."""
    token = os.getenv("ZENODO_TOKEN")
    if not token:
        raise RuntimeError("ZENODO_TOKEN environment variable is not set.")

    client = ZenodoClient(sandbox=True, token=token)
    records = client.get_records()
    metadata = _load_zenodo_json()
    if record := zenodo_find_record_by_repo_url(records):
        record = client.publish_updated_record(
            record=record, metadata=metadata, file_path=Path("book.pdf")
        )
        print(f"Zenodo record updated successfully! New ID: {record.id}.")
    else:
        record = client.publish_new_record(
            metadata=metadata, file_path=Path("book.pdf")
        )
        print(f"New Zenodo record created successfully! ID: {record.id}")
