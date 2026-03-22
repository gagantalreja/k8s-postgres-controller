import os
import json
import pytest
from unittest.mock import patch, MagicMock, call

os.environ.setdefault("PROVIDER", "aws")
os.environ.setdefault("TF_VAR_pg_admin_username", "admin")
os.environ.setdefault("TF_VAR_pg_admin_password", "secret")

from controller import handle_event, cm_watcher


def make_configmap(name, users, databases):
    cm = MagicMock()
    cm.metadata.name = name
    cm.data = {
        "users": json.dumps(users),
        "databases": json.dumps(databases),
    }
    return cm


VALID_USERS = [
    {
        "username": "alice",
        "roles": ["read"],
        "k8s_secret_options": {
            "secret_name": "alice-secret",
            "secret_namespace": "default",
        },
    }
]

VALID_DBS = [{"name": "mydb", "owner": "alice"}]


# ── handle_event ──────────────────────────────────────────────────────────────


@patch("controller.terraform_run")
@patch("builtins.open", new_callable=MagicMock)
def test_handle_event_calls_terraform_for_valid_aws_event(mock_open, mock_tf):
    import controller

    controller.CLOUD_PROVIDER = "aws"
    cm = make_configmap("my-cm", VALID_USERS, VALID_DBS)
    handle_event(cm)
    mock_tf.assert_any_call("init")
    mock_tf.assert_any_call("plan")
    mock_tf.assert_any_call("apply")


@patch("controller.terraform_run")
def test_handle_event_returns_false_for_invalid_aws_event(mock_tf):
    import controller

    controller.CLOUD_PROVIDER = "aws"
    bad_users = [
        {
            "username": "alice",
            "k8s_secret_options": {"secret_name": "s", "secret_namespace": "ns"},
        }
    ]  # missing roles
    cm = make_configmap("my-cm", bad_users, VALID_DBS)
    result = handle_event(cm)
    assert result is False
    mock_tf.assert_not_called()


@patch("controller.terraform_run")
@patch("builtins.open", new_callable=MagicMock)
def test_handle_event_calls_terraform_for_valid_gcp_event(mock_open, mock_tf):
    import controller

    controller.CLOUD_PROVIDER = "gcp"
    gcp_users = [
        {
            "username": "alice",
            "k8s_secret_options": {"secret_name": "s", "secret_namespace": "ns"},
        }
    ]
    gcp_dbs = [{"name": "mydb"}]  # no owner for gcp
    cm = make_configmap("my-cm", gcp_users, gcp_dbs)
    handle_event(cm)
    mock_tf.assert_any_call("apply")


@patch("controller.terraform_run")
def test_handle_event_returns_false_for_invalid_gcp_event(mock_tf):
    import controller

    controller.CLOUD_PROVIDER = "gcp"
    bad_dbs = [{"name": "mydb", "owner": "alice"}]  # owner not allowed in gcp
    gcp_users = [
        {
            "username": "alice",
            "k8s_secret_options": {"secret_name": "s", "secret_namespace": "ns"},
        }
    ]
    cm = make_configmap("my-cm", gcp_users, bad_dbs)
    result = handle_event(cm)
    assert result is False
    mock_tf.assert_not_called()


# ── cm_watcher ────────────────────────────────────────────────────────────────


@patch("controller.handle_event")
def test_cm_watcher_processes_matching_configmap(mock_handle):
    cm = make_configmap("my-cm", VALID_USERS, VALID_DBS)
    event = {"type": "ADDED", "object": cm}

    mock_watch = MagicMock()
    mock_watch.stream.return_value = iter([event])
    mock_v1 = MagicMock()

    cm_watcher("my-cm", "default", watch=mock_watch, v1=mock_v1)
    mock_handle.assert_called_once_with(cm)


@patch("controller.handle_event")
def test_cm_watcher_ignores_other_configmaps(mock_handle):
    cm = make_configmap("other-cm", VALID_USERS, VALID_DBS)
    event = {"type": "ADDED", "object": cm}

    mock_watch = MagicMock()
    mock_watch.stream.return_value = iter([event])
    mock_v1 = MagicMock()

    cm_watcher("my-cm", "default", watch=mock_watch, v1=mock_v1)
    mock_handle.assert_not_called()


@patch("controller.handle_event")
def test_cm_watcher_skips_deleted_events(mock_handle):
    cm = MagicMock()
    cm.metadata.name = "my-cm"
    cm.data = None  # data is None on DELETED events
    event = {"type": "DELETED", "object": cm}

    mock_watch = MagicMock()
    mock_watch.stream.return_value = iter([event])
    mock_v1 = MagicMock()

    cm_watcher("my-cm", "default", watch=mock_watch, v1=mock_v1)
    mock_handle.assert_not_called()
