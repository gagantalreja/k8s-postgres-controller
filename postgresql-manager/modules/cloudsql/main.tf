resource "random_password" "password" {
  for_each = { for user in var.users : user.username => user }
  length   = each.value.password_length
  special  = false
}

resource "google_sql_user" "users" {
  for_each        = { for user in var.users : user.username => user }
  name            = each.key
  instance        = var.instance_name
  project         = var.project_id
  password        = sensitive(random_password.password[each.key].result)
  deletion_policy = "ABANDON"
}

resource "kubernetes_secret_v1" "secret" {
  for_each = { for user in var.users : user.username => user }

  metadata {
    name      = each.value.k8s_secret_options.secret_name
    namespace = ach.value.k8s_secret_options.secret_namespace
  }

  data = {
    "${each.value.k8s_secret_options.username_key}" = each.key
    "${each.value.k8s_secret_options.username_key}" = sensitive(random_password.password[each.key].result)
  }
}


resource "google_sql_database" "databases" {
  for_each        = toset(var.databases)
  name            = each.key
  project         = var.project_id
  instance        = var.instance_name
  deletion_policy = "ABANDON"
}
