import os
import pytest

os.environ.setdefault("PROVIDER", "aws")

from controller import validation_for_aws_provider


VALID_USER = {
    "username": "alice",
    "roles": ["read"],
    "k8s_secret_options": {
        "secret_name": "alice-secret",
        "secret_namespace": "default",
    },
}

VALID_DB = {"name": "mydb", "owner": "alice"}


def test_valid_input_returns_true():
    assert validation_for_aws_provider([VALID_USER], [VALID_DB]) is True


def test_user_missing_roles_returns_false():
    user = {**VALID_USER}
    del user["roles"]
    assert validation_for_aws_provider([user], [VALID_DB]) is False


def test_user_missing_secret_name_returns_false():
    user = {
        **VALID_USER,
        "k8s_secret_options": {"secret_namespace": "default"},
    }
    assert validation_for_aws_provider([user], [VALID_DB]) is False


def test_user_missing_secret_namespace_returns_false():
    user = {
        **VALID_USER,
        "k8s_secret_options": {"secret_name": "alice-secret"},
    }
    assert validation_for_aws_provider([user], [VALID_DB]) is False


def test_database_missing_owner_returns_false():
    db = {"name": "mydb"}
    assert validation_for_aws_provider([VALID_USER], [db]) is False


def test_empty_users_and_databases_returns_true():
    # Nothing to validate, so nothing can fail
    assert validation_for_aws_provider([], []) is True