from pytest import fixture, raises

from actions.cli import app


@fixture
def _mock_zenodo_get_record(mocker):
    return mocker.patch("actions.cli.zenodo_get_record")


@fixture
def _mock_zenodo_update_record(mocker):
    return mocker.patch("actions.cli.zenodo_update_record")


@fixture
def _mock_zenodo_create_record(mocker):
    return mocker.patch("actions.cli.zenodo_create_record")


def test_zenodo_publish_existing_record(
    monkeypatch,
    _mock_zenodo_get_record,
    _mock_zenodo_create_record,
    _mock_zenodo_update_record,
):
    monkeypatch.setenv("ZENODO_TOKEN", "token")
    app("zenodo-publish", result_action="return_value")

    _mock_zenodo_update_record.assert_called_once()
    _mock_zenodo_create_record.assert_not_called()


def test_zenodo_publish_new_record(
    monkeypatch,
    _mock_zenodo_get_record,
    _mock_zenodo_create_record,
    _mock_zenodo_update_record,
):
    monkeypatch.setenv("ZENODO_TOKEN", "token")
    _mock_zenodo_get_record.return_value = None
    app("zenodo-publish", result_action="return_value")

    _mock_zenodo_create_record.assert_called_once()
    _mock_zenodo_update_record.assert_not_called()


def test_zenodo_publish_needs_token():
    with raises(RuntimeError):
        app("zenodo-publish", result_action="return_value")
