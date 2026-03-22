terraform {
  required_providers {
    postgresql = {
      source  = "jbg/postgresql"
      version = "1.19.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.7.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.38.0"
    }
  }
}

provider "postgresql" {
  host            = var.pg_hostname
  port            = 5432
  database        = "postgres"
  username        = var.pg_admin_username
  password        = var.pg_admin_password
  sslmode         = var.pg_sslmode
  connect_timeout = 15
}
