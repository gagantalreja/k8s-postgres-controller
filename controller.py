import os, json
import subprocess
import logging
from kubernetes import client, config, watch as k8s_watch

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "ERROR")),
    format="%(asctime)s :: [%(levelname)s] :: %(message)s",
)

CLOUD_PROVIDER = os.environ["PROVIDER"]
TFVARS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "terraform.tfvars.json"
)


def load_kube_config():
    """Load kubeconfiguration for Kubernetes client.
    It first tries to load in-cluster configuration, and if that fails,
    it falls back to loading the local kubeconfig file."""

    try:
        config.load_incluster_config()
        logging.info("Loaded in-cluster config")
    except config.ConfigException:
        config.load_kube_config()
        logging.info("Loaded local kubeconfig")


def validation_for_aws_provider(users: list, databases: list):
    """Validate input data for an AWS run
    Args:
        users (list): A list of user configurations.
        databases (list): A list of database configurations.
    Returns:
        bool: True if the data is valid, False otherwise.
    """

    for user in users:
        if "roles" not in user:
            logging.error(f"'roles' is expected in {user} for aws provider")
            return False

        if "secret_name" not in user["k8s_secret_options"]:
            logging.error(f"{user} entry missing 'secret_name' in 'k8s_secret_options'")
            return False

        if "secret_namespace" not in user["k8s_secret_options"]:
            logging.error(
                f"{user} entry missing 'secret_namespace' in 'k8s_secret_options'"
            )
            return False

    for db in databases:
        if "owner" not in db:
            logging.error(f"{db} entry missing 'owner'")
            return False

    return True


def validation_for_gcp_provider(users: list, databases: list):
    """Validate input data for a GCP run

    Args:
        users (list): A list of user configurations.
        databases (list): A list of database configurations.

    Returns:
        bool: True if the data is valid, False otherwise.
    """
    for user in users:
        if "roles" in user:
            logging.error(f"'roles' is not expected in {user} for gcp provider")
            return False

        if "secret_name" not in user["k8s_secret_options"]:
            logging.error(f"{user} entry missing 'secret_name' in 'k8s_secret_options'")
            return False

        if "secret_namespace" not in user["k8s_secret_options"]:
            logging.error(
                f"{user} entry missing 'secret_namespace' in 'k8s_secret_options'"
            )
            return False

    for db in databases:
        if "owner" in db:
            logging.error(f"'owner' is not expected in {db} for gcp provider")
            return False

    return True


def generate_tfvars_file(users: list, databases: list, tfvars: dict):
    """Generate a Terraform variables file based on the provided users, databases, and provider-specific configurations.

    Args:
        users (list): A list of user configurations.
        databases (list): A list of database configurations.
        tfvars (dict): A dictionary to store the generated Terraform variables.

    Returns:
        dict: The updated Terraform variables dictionary.
    """

    tfvars["users"] = users
    tfvars["databases"] = databases
    tfvars["cloud"] = CLOUD_PROVIDER

    if CLOUD_PROVIDER == "gcp":
        tfvars["gcp_project_id"] = os.getenv("GCP_PROJECT_ID")
        tfvars["cloudsql_instance_name"] = os.getenv("CLOUDSQL_INSTANCE")
    else:
        tfvars["pg_hostname"] = os.getenv("POSTGRES_HOSTNAME") or os.getenv(
            "RDS_ENDPOINT"
        )
        tfvars["pg_sslmode"] = os.getenv("POSTGRES_SSLMODE") or os.getenv("RDS_SSLMODE")

    return tfvars


def handle_event(cm):
    """Handle a ConfigMap event by validating the data and applying Terraform changes if valid."""

    users = json.loads(cm.data["users"])
    databases = json.loads(cm.data["databases"])

    if CLOUD_PROVIDER == "aws" and not validation_for_aws_provider(users, databases):
        logging.error("Validation failed for AWS provider. Skipping event.")
        return False

    if CLOUD_PROVIDER == "gcp" and not validation_for_gcp_provider(users, databases):
        logging.error("Validation failed for GCP provider. Skipping event.")
        return False

    tfvars = {}
    with open(TFVARS_PATH, "w") as varsfile:
        tfvars = generate_tfvars_file(users, databases, tfvars)
        varsfile.write(json.dumps(tfvars, indent=4))

    terraform_run("init")
    terraform_run("plan")
    terraform_run("apply")


def terraform_run(command: str, var_file_path: str = TFVARS_PATH):
    """Execute a Terraform command with the specified configuration.

    Args:
        command (str): Terraform command to execute (e.g., "plan", "apply", "destroy").
        var_file_path (str, optional): The path to the Terraform variables file.
            Defaults to "./terraform.tfvars.json".
    """

    logging.info(f"Running terraform {command}")

    env = {**os.environ}
    if CLOUD_PROVIDER != "gcp":
        env["TF_VAR_pg_admin_username"] = os.environ["TF_VAR_pg_admin_username"]
        env["TF_VAR_pg_admin_password"] = os.environ["TF_VAR_pg_admin_password"]
    else:
        env.pop("TF_VAR_pg_admin_username")
        env.pop("TF_VAR_pg_admin_password")

    cmd = ["terraform", command]
    if command != "init":
        cmd += ["-var-file", var_file_path]

    if command == "apply":
        cmd.append("-auto-approve")

    logging.info(f"Running command: {' '.join(cmd)}")

    run_directory = "./postgresql-manager/cloudsql"
    if CLOUD_PROVIDER != "gcp":
        run_directory = "./postgresql-manager/postgres"

    result = subprocess.run(
        cmd, env=env, text=True, capture_output=True, cwd=run_directory
    )

    logging.debug(result.stdout)

    if result.returncode != 0:
        logging.error(result.stderr)
        raise RuntimeError(
            f"terraform {command} failed with exit code {result.returncode}"
        )

    return result


def cm_watcher(to_watch: str, ns: str, watch: k8s_watch.Watch, v1: client.CoreV1Api):
    """Watches for changes in a ConfigMap

    Args:
        to_watch (str): The name of the ConfigMap to watch
        ns (str): The namespace of the ConfigMap
    """
    logging.info(f"Watching for changes in {to_watch} in {ns}...")
    for event in watch.stream(v1.list_namespaced_config_map, namespace=ns):
        cm = event["object"]
        if cm.metadata.name == to_watch and event["type"] != "DELETED":
            ev_type = event["type"].lower()
            logging.info(f"ConfigMap {to_watch} {ev_type}")
            handle_event(cm)


if __name__ == "__main__":

    load_kube_config()

    v1 = client.CoreV1Api()
    watch = k8s_watch.Watch()

    cm_watcher(
        os.getenv("CONFIGMAP_NAME"),
        os.getenv("CONFIGMAP_NAMESPACE"),
        watch=watch,
        v1=v1,
    )
