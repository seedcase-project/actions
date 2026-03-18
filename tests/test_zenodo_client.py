from pathlib import Path
from typing import Any

import pydantic
import pytest
import requests
from pytest import raises

from actions.examples import example_record
from actions.zenodo import (
    ZenodoClient,
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
    def _mock(json=[], status_code=200):
        return requests_mock.get(
            sandbox_client.depositions, json=json, status_code=status_code
        )

    return _mock


@pytest.fixture
def mock_get_record(requests_mock):
    record = example_record()

    def _mock(json=record.model_dump(), id=record.id, status_code=200):
        return requests_mock.get(
            f"{sandbox_client.depositions}/{id}",
            json=json,
            status_code=status_code,
        )

    return _mock


@pytest.fixture
def mock_upload_file(requests_mock):
    def _mock(url=None, json={}, file_path=Path("data.txt"), status_code=200):
        if url is None:
            url = f"{example_record().links.bucket}/{file_path.name}"
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
        [example_record(1).model_dump(), example_record(2).model_dump()]
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


# upload_file


def test_upload_file_success(mock_upload_file, tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("This is my file.")
    record = example_record(submitted=False, state="unsubmitted")
    mock = mock_upload_file()

    result = sandbox_client.upload_file(record, file_path=file_path)

    assert_headers_correct(mock)
    assert mock.last_request.body.name == str(file_path)
    assert result


def test_upload_file_failure_api(mock_upload_file, tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("This is my file.")
    record = example_record(submitted=False, state="unsubmitted")
    mock_upload_file(status_code=400)
    with raises(requests.HTTPError):
        sandbox_client.upload_file(record, file_path=file_path)

    mock_upload_file(json=[{"unexpected": "response"}])
    with raises(pydantic.ValidationError):
        sandbox_client.upload_file(record, file_path=file_path)


def test_upload_file_failure_file_not_found():
    with raises(FileNotFoundError):
        sandbox_client.upload_file(
            example_record(submitted=False, state="unsubmitted"),
            file_path=Path("data.txt"),
        )


def test_upload_file_failure_published():
    with raises(ValueError):
        sandbox_client.upload_file(
            example_record(submitted=True),
            file_path=Path("data.txt"),
        )


def test_upload_file_failure_no_bucket():
    with raises(ValueError):
        sandbox_client.upload_file(
            example_record(submitted=False, state="unsubmitted", bucket=None),
            file_path=Path("data.txt"),
        )
