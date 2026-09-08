from typing import Any, Dict, Tuple

class JSONSchemaValidationError(Exception):
    pass

def validate_json_payload(payload: Any, expected_schema: Dict[str, Any] = None) -> Tuple[bool, str]:
    """
    Validates input or output payload against a simple structural JSON schema constraint.
    """
    if expected_schema is None:
        return True, ""

    schema_type = expected_schema.get("type")
    if schema_type == "object" and not isinstance(payload, dict):
        return False, f"Expected JSON object (dict), received {type(payload).__name__}"
    elif schema_type == "array" and not isinstance(payload, list):
        return False, f"Expected JSON array (list), received {type(payload).__name__}"
    elif schema_type == "string" and not isinstance(payload, str):
        return False, f"Expected string, received {type(payload).__name__}"

    required_fields = expected_schema.get("required", [])
    if isinstance(payload, dict) and required_fields:
        missing = [f for f in required_fields if f not in payload]
        if missing:
            return False, f"Missing required payload keys: {', '.join(missing)}"

    return True, ""
