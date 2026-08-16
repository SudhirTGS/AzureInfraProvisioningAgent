from app.tools.validators import validate_field, validate_requirements

VALID_REQUIREMENTS = {
    "resource_group": "rg-prod-data",
    "region": "eastus",
    "sql_server_name": "sql-prod-eastus-01",
    "database_name": "appdb",
    "edition": "GeneralPurpose",
    "service_objective": "GP_Gen5_4",
    "license_type": "LicenseIncluded",
    "environment_tag": "prod",
}


def test_validate_field_valid_region():
    result = validate_field("azure_sql_database", "region", "eastus")
    assert result["valid"] is True


def test_validate_field_invalid_region_reports_options():
    result = validate_field("azure_sql_database", "region", "brazilsouth")
    assert result["valid"] is False
    assert "eastus" in result["valid_options"]


def test_validate_field_invalid_pattern():
    result = validate_field("azure_sql_database", "sql_server_name", "Invalid_Name!")
    assert result["valid"] is False
    assert "expected_pattern" in result


def test_validate_requirements_missing_fields():
    result = validate_requirements("azure_sql_database", {"region": "eastus"})
    assert result["valid"] is False
    assert any("resource_group" in e for e in result["errors"])


def test_validate_requirements_edition_service_objective_mismatch():
    bad = {**VALID_REQUIREMENTS, "edition": "Standard", "service_objective": "GP_Gen5_4"}
    result = validate_requirements("azure_sql_database", bad)
    assert result["valid"] is False
    assert any("service_objective" in e for e in result["errors"])


def test_validate_requirements_success_fills_defaults():
    result = validate_requirements("azure_sql_database", VALID_REQUIREMENTS)
    assert result["valid"] is True
    normalized = result["normalized_requirements"]
    assert normalized["max_size_gb"] == 32
    assert normalized["backup_redundancy"] == "Local"


def test_validate_requirements_max_size_exceeds_basic_limit():
    bad = {
        **VALID_REQUIREMENTS,
        "edition": "Basic",
        "service_objective": "Basic",
        "max_size_gb": 32,
    }
    result = validate_requirements("azure_sql_database", bad)
    assert result["valid"] is False
    assert any("max_size_gb" in e for e in result["errors"])


def test_validate_requirements_basic_default_max_size_is_capped():
    basic = {
        **VALID_REQUIREMENTS,
        "edition": "Basic",
        "service_objective": "Basic",
    }
    result = validate_requirements("azure_sql_database", basic)
    assert result["valid"] is True
    assert result["normalized_requirements"]["max_size_gb"] == 2
