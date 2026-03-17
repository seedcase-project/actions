from http import HTTPStatus
from pathlib import Path

from pytest import MonkeyPatch, fixture, raises
from requests import HTTPError
from requests_mock import ANY

from actions.examples import example_metadata, example_record
from actions.zenodo import (
    ZenodoRelatedIdentifier,
    zenodo_get_record,
)


@fixture
def _zenodo_json(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".zenodo.json").write_text(example_metadata().model_dump_json())


def test_returns_record_if_matching_record_has_exactly_one_matching_identifier(
    requests_mock, _zenodo_json
):
    requests_mock.get(
        url=ANY,
        json=[
            example_record(id=12).model_dump(),
            example_record(repo_url="https://github.com/another-repo").model_dump(),
        ],
    )

    record = zenodo_get_record("token")

    assert record
    assert record.id == 12


def test_returns_record_if_matching_record_has_at_least_one_matching_identifier(
    requests_mock, _zenodo_json
):
    fetched_record = example_record(id=12)
    fetched_record.metadata.related_identifiers.extend(
        [
            # Duplicate identifier
            fetched_record.metadata.related_identifiers[0],
            # Different identifier
            ZenodoRelatedIdentifier(
                identifier="https://github.com/another-repo",
                relation="IsDerivedFrom",
                resource_type="other",
            ),
        ]
    )
    requests_mock.get(url=ANY, json=[fetched_record.model_dump()])

    record = zenodo_get_record("token")

    assert record
    assert record.id == 12


def test_raises_error_if_multiple_matching_records(requests_mock, _zenodo_json):
    requests_mock.get(
        url=ANY,
        json=[example_record(id=12).model_dump(), example_record(id=13).model_dump()],
    )

    with raises(ValueError):
        zenodo_get_record("token")


def test_returns_none_if_no_records_on_zenodo(requests_mock, _zenodo_json):
    requests_mock.get(url=ANY, json=[])

    record = zenodo_get_record("token")

    assert record is None


def test_returns_none_if_no_matching_records(requests_mock, _zenodo_json):
    requests_mock.get(
        url=ANY,
        json=[example_record(repo_url="https://github.com/another-repo").model_dump()],
    )

    record = zenodo_get_record("token")

    assert record is None


def test_raises_error_if_request_unsuccessful(requests_mock, _zenodo_json):
    requests_mock.get(url=ANY, status_code=HTTPStatus.BAD_REQUEST)

    with raises(HTTPError):
        zenodo_get_record("token")


def test_raises_error_if_zenodo_json_has_no_repo_url(monkeypatch, tmp_path):
    metadata = example_metadata()
    monkeypatch.chdir(tmp_path)
    del metadata.related_identifiers[0]
    (tmp_path / ".zenodo.json").write_text(metadata.model_dump_json())

    with raises(ValueError):
        zenodo_get_record("token")


def test_raises_error_if_zenodo_json_has_multiple_repo_urls(monkeypatch, tmp_path):
    metadata = example_metadata()
    monkeypatch.chdir(tmp_path)
    metadata.related_identifiers.append(
        ZenodoRelatedIdentifier(
            identifier="https://github.com/another-repo",
            relation="IsDerivedFrom",
            resource_type="other",
        )
    )
    (tmp_path / ".zenodo.json").write_text(metadata.model_dump_json())

    with raises(ValueError):
        zenodo_get_record("token")
