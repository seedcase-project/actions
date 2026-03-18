from typing import Any

import pydantic
import pytest
import requests
from pytest import mark, raises

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
def mock_make_editable(requests_mock):
    record = example_record()

    def _mock(json=record.model_dump(), id=record.id, status_code=201):
        return requests_mock.post(
            f"{sandbox_client.depositions}/{id}/actions/edit",
            json=json,
            status_code=status_code,
        )

    return _mock


@pytest.fixture
def mock_discard_draft(requests_mock):
    def _mock(id=example_record().id, status_code=204):
        return requests_mock.post(
            f"{sandbox_client.depositions}/{id}/actions/discard",
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


# make_editable


@mark.parametrize("state", ["inprogress", "unsubmitted"])
def test_make_editable_success_when_editable(mock_make_editable, state):
    record = example_record(state=state)
    mock = mock_make_editable()

    result = sandbox_client.make_editable(record)

    assert not mock.called
    assert result.id == record.id


def test_make_editable_success_when_not_editable(mock_make_editable):
    record = example_record(state="done")
    mock = mock_make_editable()

    result = sandbox_client.make_editable(record)

    assert_headers_correct(mock)
    assert result.id == record.id


def test_make_editable_failure(mock_make_editable):
    record = example_record()
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

    sandbox_client.discard_draft(example_record(state=state))

    assert_headers_correct(mock)


def test_discard_draft_success_when_not_editable(mock_discard_draft):
    mock = mock_discard_draft()

    sandbox_client.discard_draft(example_record(state="done"))

    assert not mock.called


def test_discard_draft_failure(mock_discard_draft):
    mock_discard_draft(status_code=400)
    with raises(requests.HTTPError):
        sandbox_client.discard_draft(example_record(state="inprogress"))
