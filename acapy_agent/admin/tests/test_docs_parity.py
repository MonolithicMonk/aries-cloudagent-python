from acapy_agent.connections.v2.models import (
    ConnectionMetadataSetRequestSchema,
    ConnectionStaticRequestSchema,
    ConnRecordSchema,
    EndpointsResultSchema,
)


def check_model_examples(model_class, fields_to_check):
    """Helper to verify examples exist in JSON schema."""
    schema = model_class.model_json_schema()
    props = schema.get("properties", {})

    for field_name in fields_to_check:
        # Check if field exists in schema (using CamelCase name)
        assert field_name in props, (
            f"Field {field_name} missing from {model_class.__name__} schema"
        )

        field_schema = props[field_name]
        has_examples = False

        # 1. Check Outer Schema (Field level examples)
        if "examples" in field_schema and field_schema["examples"]:
            if field_schema["examples"][0] != "string":
                has_examples = True

        # 2. Check Inner Schema (Type level examples inside AnyOf)
        if not has_examples and "anyOf" in field_schema:
            for sub_schema in field_schema["anyOf"]:
                if sub_schema.get("type") == "null":
                    continue
                if "examples" in sub_schema and sub_schema["examples"]:
                    if sub_schema["examples"][0] != "string":
                        has_examples = True
                        break

        assert has_examples, (
            f"Field {field_name} in {model_class.__name__} is missing 'examples'"
        )


def check_model_title(model_class, expected_title):
    """Helper to verify model title matches legacy name."""
    schema = model_class.model_json_schema()
    assert schema.get("title") == expected_title, (
        f"Model {model_class.__name__} has title '{schema.get('title')}', "
        f"expected '{expected_title}'"
    )


def test_connection_static_request_parity():
    """Ensure ConnectionStaticRequest has rich examples matching Legacy API."""
    fields = [
        "alias",
        "myDid",
        "mySeed",
        "theirDid",
        "theirEndpoint",
        "theirLabel",
        "theirSeed",
        "theirVerkey",
    ]
    check_model_examples(ConnectionStaticRequestSchema, fields)
    check_model_title(ConnectionStaticRequestSchema, "ConnectionStaticRequest")


def test_connection_metadata_request_parity():
    """Ensure Metadata request has examples."""
    check_model_examples(ConnectionMetadataSetRequestSchema, ["metadata"])
    check_model_title(
        ConnectionMetadataSetRequestSchema, "ConnectionMetadataSetRequest"
    )


def test_endpoints_result_parity():
    """Ensure Endpoints result has examples."""
    check_model_examples(EndpointsResultSchema, ["myEndpoint", "theirEndpoint"])
    check_model_title(EndpointsResultSchema, "EndpointsResult")


def test_conn_record_parity():
    """Ensure ConnRecord has correct title."""
    check_model_title(ConnRecordSchema, "ConnRecord")
