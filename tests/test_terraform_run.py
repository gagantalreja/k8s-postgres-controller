import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("PROVIDER", "aws")
os.environ.setdefault("TF_VAR_pg_admin_username", "admin")
os.environ.setdefault("TF_VAR_pg_admin_password", "secret")

from controller import terraform_run


def make_mock_result(returncode=0):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = "output"
    result.stderr = "error"
    return result


@patch("controller.subprocess.run")
def test_init_does_not_pass_var_file(mock_run):
    mock_run.return_value = make_mock_result()
    terraform_run("init")
    cmd = mock_run.call_args[0][0]
    assert "-var-file" not in " ".join(cmd)


@patch("controller.subprocess.run")
def test_plan_passes_var_file(mock_run):
    mock_run.return_value = make_mock_result()
    terraform_run("plan")
    cmd = mock_run.call_args[0][0]
    assert "-var-file" in cmd


@patch("controller.subprocess.run")
def test_apply_includes_auto_approve(mock_run):
    mock_run.return_value = make_mock_result()
    terraform_run("apply")
    cmd = mock_run.call_args[0][0]
    assert "-auto-approve" in cmd


@patch("controller.subprocess.run")
def test_plan_does_not_include_auto_approve(mock_run):
    mock_run.return_value = make_mock_result()
    terraform_run("plan")
    cmd = mock_run.call_args[0][0]
    assert "-auto-approve" not in cmd


@patch("controller.subprocess.run")
def test_failed_command_raises_runtime_error(mock_run):
    mock_run.return_value = make_mock_result(returncode=1)
    with pytest.raises(RuntimeError, match="terraform plan failed"):
        terraform_run("plan")


@patch("controller.subprocess.run")
def test_aws_env_includes_pg_credentials(mock_run):
    mock_run.return_value = make_mock_result()
    import controller
    controller.CLOUD_PROVIDER = "aws"
    terraform_run("plan")
    env = mock_run.call_args[1]["env"]
    assert "TF_VAR_pg_admin_username" in env
    assert "TF_VAR_pg_admin_password" in env


@patch("controller.subprocess.run")
def test_gcp_env_excludes_pg_credentials(mock_run):
    mock_run.return_value = make_mock_result()
    import controller
    controller.CLOUD_PROVIDER = "gcp"
    terraform_run("plan")
    env = mock_run.call_args[1]["env"]
    assert "TF_VAR_pg_admin_username" not in env
    assert "TF_VAR_pg_admin_password" not in env