from app.tools.schema_loader import get_resource_schema, list_available_resource_types


def test_lists_azure_sql_database():
    assert "azure_sql_database" in list_available_resource_types()


def test_get_resource_schema_returns_full_schema():
    schema = get_resource_schema("azure_sql_database")
    assert schema["resource_type"] == "azure_sql_database"
    assert "region" in schema["required_fields"]
    assert "max_size_gb" in schema["optional_fields"]


def test_get_resource_schema_unknown_type_reports_supported_types():
    schema = get_resource_schema("azure_kubernetes_cluster")
    assert "error" in schema
    assert "azure_sql_database" in schema["supported_resource_types"]
