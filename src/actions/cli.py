import os

from cyclopts import App

from actions.zenodo import (
    zenodo_create_record,
    zenodo_record_exists,
    zenodo_update_record,
)

app = App(
    name="actions",
    help=(
        "The `actions` package contains GitHub reusable workflows and "
        "actions used in the Seedcase Project."
    ),
)


@app.command()
def zenodo_publish() -> None:
    """Publish a new version of the repository on Zenodo."""
    token = os.getenv("ZENODO_TOKEN")
    if not token:
        raise RuntimeError("ZENODO_TOKEN environment variable is not set.")

    if zenodo_record_exists(token):
        zenodo_update_record(token)
        print("Zenodo record updated successfully!")
    else:
        zenodo_create_record(token)
        print("New Zenodo record created successfully!")
