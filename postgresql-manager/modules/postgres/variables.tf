variable "roles" {
  description = "list of users to create"
  type = list(object({
    username        = string
    roles           = list(string)
    create_database = optional(bool, true)
    create_role     = optional(bool, true)
    login           = optional(bool, true)
    password_length = optional(number, 16)
    k8s_secret_options = object({
      secret_name      = string
      secret_namespace = string
      username_key     = string
      password_key     = string
    })
  }))
}

variable "databases" {
  description = "list of databases to create"
  type = list(object({
    name  = string
    owner = optional(string)
  }))
}


variable "pg_hostname" {
  description = "rds hostname"
  type        = string
}

variable "pg_sslmode" {
  description = "RDS sslmode"
  type        = string
}

variable "pg_admin_username" {
  description = "admin username for rds instance"
  type        = string
  sensitive   = true
}

variable "pg_admin_password" {
  description = "admin password for rds instance"
  type        = string
  sensitive   = true
}
