import os
import pytest

os.environ.setdefault("PROVIDER", "gcp")

from controller import validation_for_gcp_provider


VALID_USER = {
    "username": "alice",
    "k8s_secret_options": {
        "secret_name": "alice-secret",
        "secret_namespace": "default",
    },
}

VALID_DB = {"name": "mydb"}


def test_valid_input_returns_true():
    assert validation_for_gcp_provider([VALID_USER], [VALID_DB]) is True


def test_user_with_roles_returns_false():
    user = {**VALID_USER, "roles": ["read"]}
    assert validation_for_gcp_provider([user], [VALID_DB]) is False


def test_user_missing_secret_name_returns_false():
    user = {
        **VALID_USER,
        "k8s_secret_options": {"secret_namespace": "default"},
    }
    assert validation_for_gcp_provider([user], [VALID_DB]) is False


def test_user_missing_secret_namespace_returns_false():
    user = {
        **VALID_USER,
        "k8s_secret_options": {"secret_name": "alice-secret"},
    }
    assert validation_for_gcp_provider([user], [VALID_DB]) is False


def test_database_with_owner_returns_false():
    db = {"name": "mydb", "owner": "alice"}
    assert validation_for_gcp_provider([VALID_USER], [db]) is False


def test_empty_users_and_databases_returns_true():
    assert validation_for_gcp_provider([], []) is True