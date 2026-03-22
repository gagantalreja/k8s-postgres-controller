import os
import pytest
from unittest.mock import patch

os.environ.setdefault("PROVIDER", "aws")

from controller import generate_tfvars_file


USERS = [{"username": "alice"}]
DATABASES = [{"name": "mydb"}]


def test_aws_tfvars_contains_base_keys():
    with patch.dict(os.environ, {"PROVIDER": "aws", "POSTGRES_HOSTNAME": "db.host", "POSTGRES_SSLMODE": "require"}):
        import controller
        controller.CLOUD_PROVIDER = "aws"
        result = generate_tfvars_file(USERS, DATABASES, {})

    assert result["users"] == USERS
    assert result["databases"] == DATABASES
    assert result["cloud"] == "aws"


def test_aws_tfvars_uses_postgres_hostname():
    with patch.dict(os.environ, {"PROVIDER": "aws", "POSTGRES_HOSTNAME": "db.host", "POSTGRES_SSLMODE": "require"}):
        import controller
        controller.CLOUD_PROVIDER = "aws"
        result = generate_tfvars_file(USERS, DATABASES, {})

    assert result["pg_hostname"] == "db.host"
    assert result["pg_sslmode"] == "require"


def test_aws_tfvars_falls_back_to_rds_env_vars():
    env = {"PROVIDER": "aws", "RDS_ENDPOINT": "rds.host", "RDS_SSLMODE": "verify-full"}
    with patch.dict(os.environ, env, clear=True):
        import controller
        controller.CLOUD_PROVIDER = "aws"
        result = generate_tfvars_file(USERS, DATABASES, {})

    assert result["pg_hostname"] == "rds.host"
    assert result["pg_sslmode"] == "verify-full"


def test_gcp_tfvars_contains_gcp_keys():
    env = {"PROVIDER": "gcp", "GCP_PROJECT_ID": "my-project", "CLOUDSQL_INSTANCE": "my-instance"}
    with patch.dict(os.environ, env):
        import controller
        controller.CLOUD_PROVIDER = "gcp"
        result = generate_tfvars_file(USERS, DATABASES, {})

    assert result["gcp_project_id"] == "my-project"
    assert result["cloudsql_instance_name"] == "my-instance"
    assert "pg_hostname" not in result


def test_gcp_tfvars_no_postgres_keys():
    env = {"PROVIDER": "gcp", "GCP_PROJECT_ID": "my-project", "CLOUDSQL_INSTANCE": "my-instance"}
    with patch.dict(os.environ, env):
        import controller
        controller.CLOUD_PROVIDER = "gcp"
        result = generate_tfvars_file(USERS, DATABASES, {})

    assert "pg_hostname" not in result
    assert "pg_sslmode" not in result