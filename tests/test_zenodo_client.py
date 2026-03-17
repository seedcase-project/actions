from pathlib import Path
from typing import Any, Optional

import pydantic
import pytest
import requests
from pytest import mark, raises

from actions.zenodo import (
    ZenodoClient,
    ZenodoCreator,
    ZenodoLinks,
    ZenodoMetadata,
    ZenodoRecord,
    ZenodoRecordState,
    ZenodoRelatedIdentifier,
)


def _make_metadata(title: str = "Test Poster") -> ZenodoMetadata:
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


def _make_record(
    id: int = 123,
    metadata: ZenodoMetadata = _make_metadata(),
    state: ZenodoRecordState = "done",
    submitted: bool = True,
    bucket: Optional[str] = "https://path.com/path/wrwee-324-23f-sdf",
) -> ZenodoRecord:
    return ZenodoRecord(
        id=id,
        metadata=metadata,
        state=state,
        submitted=submitted,
        links=ZenodoLinks(latest_draft="https://path.com/path/9999", bucket=bucket),
    )


sandbox_client = ZenodoClient(sandbox=True, token="token")


def test_creates_client_for_sandbox_api():
    assert sandbox_client.depositions.startswith("https://sandbox.zenodo")
    assert "token" in sandbox_client.headers["Authorization"]


def test_creates_client_for_real_api():
    client = ZenodoClient(sandbox=False, token="token")

    assert client.depositions.startswith("https://zenodo")
    assert "token" in client.headers["Authorization"]


# Endpoints


def assert_headers_correct(mock: Any) -> None:
    assert mock.called
    request = mock.last_request
    assert request.headers["Authorization"] == sandbox_client.headers["Authorization"]


@pytest.fixture
def mock_get_records(requests_mock):
    def _mock(json={}, status_code=200):
        return requests_mock.get(
            sandbox_client.depositions, json=json, status_code=status_code
        )

    return _mock


@pytest.fixture
def mock_get_record(requests_mock):
    def _mock(json=_make_record().model_dump(), status_code=200):
        return requests_mock.get(
            f"{sandbox_client.depositions}/{json['id']}",
            json=json,
            status_code=status_code,
        )

    return _mock


@pytest.fixture
def mock_create_record(requests_mock):
    def _mock(json=_make_record().model_dump(), status_code=200):
        return requests_mock.post(
            sandbox_client.depositions, json=json, status_code=status_code
        )

    return _mock


@pytest.fixture
def mock_make_editable(requests_mock):
    def _mock(json=_make_record().model_dump(), status_code=200):
        return requests_mock.post(
            f"{sandbox_client.depositions}/{json['id']}/actions/edit",
            json=json,
            status_code=status_code,
        )

    return _mock


@pytest.fixture
def mock_update_metadata(requests_mock):
    def _mock(json=_make_record().model_dump(), status_code=200):
        return requests_mock.put(
            f"{sandbox_client.depositions}/{json['id']}",
            json=json,
            status_code=status_code,
        )

    return _mock


@pytest.fixture
def mock_discard_draft(requests_mock):
    def _mock(record_id=_make_record().id, status_code=204):
        return requests_mock.post(
            f"{sandbox_client.depositions}/{record_id}/actions/discard",
            status_code=status_code,
        )

    return _mock


@pytest.fixture
def mock_upload_file(requests_mock):
    def _mock(url=None, json={}, file_path=Path("data.txt"), status_code=200):
        if url is None:
            url = f"{_make_record().links.bucket}/{file_path.name}"
        return requests_mock.put(
            url,
            json=json,
            status_code=status_code,
        )

    return _mock


# get_records


def test_get_records_success(mock_get_records):
    mock_get_records([])
    result = sandbox_client.get_records()
    assert result == []

    mock = mock_get_records(
        [_make_record(1).model_dump(), _make_record(2).model_dump()]
    )
    result = sandbox_client.get_records()
    assert_headers_correct(mock)
    assert len(result) == 2
    assert result[0].id == 1
    assert result[1].id == 2


def test_get_records_failure(mock_get_records):
    mock_get_records(status_code=500)
    with raises(requests.HTTPError):
        sandbox_client.get_records()

    mock_get_records([{"unexpected": "response"}])
    with raises(pydantic.ValidationError):
        sandbox_client.get_records()


# get_record


def test_get_record_success(mock_get_record):
    mock = mock_get_record()

    result = sandbox_client.get_record(123)

    assert_headers_correct(mock)
    assert result.id == 123


def test_get_record_failure(mock_get_record):
    mock_get_record(status_code=500)
    with raises(requests.HTTPError):
        sandbox_client.get_record(123)

    mock_get_record({"unexpected": "response"})
    with raises(pydantic.ValidationError):
        sandbox_client.get_record(123)


# create_record


def test_create_record_success(mock_create_record):
    metadata = _make_metadata()
    mock = mock_create_record()

    result = sandbox_client.create_record(metadata)

    assert_headers_correct(mock)
    assert result.id == 123
    assert mock.last_request.json()["metadata"] == metadata.model_dump()


def test_create_record_failure(mock_create_record):
    metadata = _make_metadata()
    mock_create_record(status_code=400)
    with raises(requests.HTTPError):
        sandbox_client.create_record(metadata)

    mock_create_record({"unexpected": "response"})
    with raises(pydantic.ValidationError):
        sandbox_client.create_record(metadata)


# update_metadata


def test_update_metadata_success(mock_make_editable, mock_update_metadata):
    old_record = _make_record()
    updated_metadata = _make_metadata(title="new title")
    updated_record = _make_record(metadata=updated_metadata).model_dump()
    mock_make_editable()
    mock = mock_update_metadata(updated_record)

    result = sandbox_client.update_metadata(old_record, updated_metadata)

    assert_headers_correct(mock)
    assert result.metadata.title == updated_metadata.title


def test_update_metadata_failure(mock_make_editable, mock_update_metadata):
    mock_make_editable()
    record = _make_record()
    mock_update_metadata(status_code=400)
    with raises(requests.HTTPError):
        sandbox_client.update_metadata(record, record.metadata)

    mock_update_metadata({"unexpected": "response"})
    with raises(pydantic.ValidationError):
        sandbox_client.update_metadata(record, record.metadata)


# make_editable


@mark.parametrize("state", ["inprogress", "unsubmitted"])
def test_make_editable_success_when_editable(mock_make_editable, state):
    record = _make_record(state=state)
    mock = mock_make_editable()

    result = sandbox_client.make_editable(record)

    assert not mock.called
    assert result.id == record.id


def test_make_editable_success_when_not_editable(mock_make_editable):
    record = _make_record(state="done")
    mock = mock_make_editable(record.model_dump())

    result = sandbox_client.make_editable(record)

    assert_headers_correct(mock)
    assert result.id == record.id


def test_make_editable_failure(mock_make_editable):
    record = _make_record()
    mock_make_editable(status_code=400)
    with raises(requests.HTTPError):
        sandbox_client.make_editable(record)

    mock_make_editable({"unexpected": "response"})
    with raises(pydantic.ValidationError):
        sandbox_client.make_editable(record)


# discard_draft


@mark.parametrize("state", ["inprogress", "unsubmitted"])
def test_discard_draft_success_when_editable(mock_discard_draft, state):
    mock = mock_discard_draft()

    sandbox_client.discard_draft(_make_record(state=state))

    assert_headers_correct(mock)


def test_discard_draft_success_when_not_editable(mock_discard_draft):
    mock = mock_discard_draft()

    sandbox_client.discard_draft(_make_record(state="done"))

    assert not mock.called


def test_discard_draft_failure(mock_discard_draft):
    mock_discard_draft(status_code=400)
    with raises(requests.HTTPError):
        sandbox_client.discard_draft(_make_record(state="inprogress"))


# upload_file


def test_upload_file_success(mock_upload_file, tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("This is my file.")
    record = _make_record(submitted=False, state="unsubmitted")
    mock = mock_upload_file()

    result = sandbox_client.upload_file(record, file_path=file_path)

    assert_headers_correct(mock)
    assert result


def test_upload_file_failure_api(mock_upload_file, tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("This is my file.")
    record = _make_record(submitted=False, state="unsubmitted")
    mock_upload_file(status_code=400)
    with raises(requests.HTTPError):
        sandbox_client.upload_file(record, file_path=file_path)

    mock_upload_file(json=[{"unexpected": "response"}])
    with raises(pydantic.ValidationError):
        sandbox_client.upload_file(record, file_path=file_path)


def test_upload_file_failure_file_not_found():
    with raises(FileNotFoundError):
        sandbox_client.upload_file(
            _make_record(submitted=False, state="unsubmitted"),
            file_path=Path("data.txt"),
        )


def test_upload_file_failure_published():
    with raises(ValueError):
        sandbox_client.upload_file(
            _make_record(submitted=True),
            file_path=Path("data.txt"),
        )


def test_upload_file_failure_no_bucket():
    with raises(ValueError):
        sandbox_client.upload_file(
            _make_record(submitted=False, state="unsubmitted", bucket=None),
            file_path=Path("data.txt"),
        )
