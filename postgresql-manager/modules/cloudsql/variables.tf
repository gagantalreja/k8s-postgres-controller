variable "users" {
  description = "list of users to create"
  type = list(object({
    username        = string
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
  type        = list(string)
}

variable "instance_name" {
  description = "cloudsql instance name"
  type        = string
}

variable "project_id" {
  description = "gcp project id"
  type        = string
}
