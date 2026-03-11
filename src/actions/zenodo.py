def zenodo_record_exists(token: str) -> bool:  # noqa: ARG001
    """Check whether a Zenodo concept record already exists for the repository.

    Args:
        token: Zenodo API access token.

    Returns:
        True if a concept record already exists for the repository,
        otherwise False.
    """
    return False


def zenodo_create_record(token: str) -> None:
    """Create a new Zenodo concept record and publish the first version.

    Args:
        token: Zenodo API access token.
    """
    ...


def zenodo_update_record(token: str) -> None:
    """Publish a new version of an existing Zenodo concept record.

    Args:
        token: Zenodo API access token.
    """
    ...
