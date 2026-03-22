resource "random_password" "password" {
  for_each = { for role in var.roles : role.username => role }
  length   = each.value.password_length
  special  = false
}

resource "postgresql_role" "role" {
  for_each        = { for role in var.roles : role.username => role }
  name            = each.key
  password        = sensitive(random_password.password[each.key].result)
  roles           = each.value.roles
  login           = each.value.login
  create_database = each.value.create_database
  create_role     = each.value.create_role
}

resource "kubernetes_secret_v1" "secret" {
  for_each = { for role in var.roles : role.username => role }

  metadata {
    name      = each.value.k8s_secret_options.secret_name
    namespace = ach.value.k8s_secret_options.secret_namespace
  }

  data = {
    "${each.value.k8s_secret_options.username_key}" = each.key
    "${each.value.k8s_secret_options.username_key}" = sensitive(random_password.password[each.key].result)
  }
}

resource "postgresql_database" "databases" {
  for_each = { for db in var.databases : db.name => db }
  name     = each.key
  owner    = each.value.owner
}
