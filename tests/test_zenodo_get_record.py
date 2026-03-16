from http import HTTPStatus
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch, fixture, raises
from requests import HTTPError
from requests_mock import ANY

from actions.zenodo import (
    ZenodoCreator,
    ZenodoLinks,
    ZenodoMetadata,
    ZenodoRecord,
    ZenodoRelatedIdentifier,
    zenodo_get_record,
)


@fixture
def _zenodo_metadata() -> ZenodoMetadata:
    return ZenodoMetadata(
        title="Test Repo",
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


@fixture
def _zenodo_json(
    monkeypatch: MonkeyPatch, tmp_path: Path, _zenodo_metadata: ZenodoMetadata
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".zenodo.json").write_text(_zenodo_metadata.model_dump_json())


def _make_record(
    record_id: int = 123, repo_url: str = "https://github.com/test-repo"
) -> dict[str, Any]:
    record = ZenodoRecord(
        id=record_id,
        metadata=ZenodoMetadata(
            title="Test Repo",
            upload_type="poster",
            creators=[
                ZenodoCreator(
                    name="Doe, Jane", affiliation="University of Testfalia", orcid="ABC"
                )
            ],
            related_identifiers=[
                ZenodoRelatedIdentifier(
                    identifier=repo_url,
                    relation="IsDerivedFrom",
                    resource_type="other",
                )
            ],
        ),
        links=ZenodoLinks(),
    )
    return record.model_dump()


def test_returns_record_if_matching_record_has_exactly_one_matching_identifier(
    requests_mock, _zenodo_json
):
    requests_mock.get(
        url=ANY,
        json=[
            _make_record(record_id=12),
            _make_record(repo_url="https://github.com/another-repo"),
        ],
    )

    record = zenodo_get_record("token")

    assert record
    assert record.id == 12


def test_returns_record_if_matching_record_has_at_least_one_matching_identifier(
    requests_mock, _zenodo_json
):
    fetched_record = _make_record(record_id=12)
    # Duplicate identifier
    fetched_record["metadata"]["related_identifiers"] *= 2
    # Different identifier
    fetched_record["metadata"]["related_identifiers"].append(
        {
            "identifier": "https://github.com/another-repo",
            "relation": "IsDerivedFrom",
            "resource_type": "other",
        }
    )
    requests_mock.get(url=ANY, json=[fetched_record])

    record = zenodo_get_record("token")

    assert record
    assert record.id == 12


def test_raises_error_if_multiple_matching_records(requests_mock, _zenodo_json):
    requests_mock.get(
        url=ANY, json=[_make_record(record_id=12), _make_record(record_id=13)]
    )

    with raises(ValueError):
        zenodo_get_record("token")


def test_returns_none_if_no_records_on_zenodo(requests_mock, _zenodo_json):
    requests_mock.get(url=ANY, json=[])

    record = zenodo_get_record("token")

    assert record is None


def test_returns_none_if_no_matching_records(requests_mock, _zenodo_json):
    requests_mock.get(
        url=ANY, json=[_make_record(repo_url="https://github.com/another-repo")]
    )

    record = zenodo_get_record("token")

    assert record is None


def test_raises_error_if_request_unsuccessful(requests_mock, _zenodo_json):
    requests_mock.get(url=ANY, status_code=HTTPStatus.BAD_REQUEST)

    with raises(HTTPError):
        zenodo_get_record("token")


def test_raises_error_if_zenodo_json_has_no_repo_url(
    _zenodo_metadata, monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    del _zenodo_metadata.related_identifiers[0]
    (tmp_path / ".zenodo.json").write_text(_zenodo_metadata.model_dump_json())

    with raises(ValueError):
        zenodo_get_record("token")


def test_raises_error_if_zenodo_json_has_multiple_repo_urls(
    _zenodo_metadata, monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    _zenodo_metadata.related_identifiers.append(
        ZenodoRelatedIdentifier(
            identifier="https://github.com/another-repo",
            relation="IsDerivedFrom",
            resource_type="other",
        )
    )
    (tmp_path / ".zenodo.json").write_text(_zenodo_metadata.model_dump_json())

    with raises(ValueError):
        zenodo_get_record("token")
