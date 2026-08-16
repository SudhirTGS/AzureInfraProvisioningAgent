from app.submission.terraform_renderer import compute_slug, render_resource

NORMALIZED = {
    "resource_group": "rg-prod-data",
    "region": "eastus",
    "sql_server_name": "sql-prod-eastus-01",
    "database_name": "appdb",
    "edition": "GeneralPurpose",
    "service_objective": "GP_Gen5_4",
    "license_type": "LicenseIncluded",
    "environment_tag": "prod",
    "max_size_gb": 32,
    "backup_redundancy": "Local",
    "firewall_rules": [],
}


def test_compute_slug_is_deterministic_and_readable():
    slug = compute_slug("azure_sql_database", NORMALIZED)
    assert slug == "sql-prod-eastus-01-appdb"


def test_render_resource_produces_expected_files():
    rendered = render_resource("azure_sql_database", NORMALIZED)
    assert set(rendered) == {
        "backend.tf",
        "variables.tf",
        "main.tf",
        "terraform.tfvars",
        "provider.tf",
    }
    assert "azurerm_mssql_server" in rendered["main.tf"]
    assert "azurerm_mssql_database" in rendered["main.tf"]
    assert "azurerm_mssql_firewall_rule" not in rendered["main.tf"]
    assert 'sql_server_name   = "sql-prod-eastus-01"' in rendered["terraform.tfvars"]

    # SQL auth only — no Azure AD admin block, password sourced from a
    # variable that's never rendered into tfvars.
    assert "administrator_login " in rendered["main.tf"]
    assert "administrator_login_password" in rendered["main.tf"]
    assert "azuread_administrator" not in rendered["main.tf"]
    assert "sql_admin_password =" not in rendered["terraform.tfvars"]


def test_render_resource_includes_firewall_rules_when_present():
    with_rules = {
        **NORMALIZED,
        "firewall_rules": [{"name": "office", "start_ip_address": "1.2.3.4", "end_ip_address": "1.2.3.4"}],
    }
    rendered = render_resource("azure_sql_database", with_rules)
    assert "azurerm_mssql_firewall_rule" in rendered["main.tf"]
