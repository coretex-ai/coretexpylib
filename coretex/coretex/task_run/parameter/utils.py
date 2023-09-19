from typing import Optional, Any, Tuple


def validateEnumStructure(name: str, value: Optional[Any], required: bool) -> Tuple[bool, Optional[str]]:
    if not isinstance(value, dict):
        return False, None

    # Enum parameter must contain 2 key-value pairs: selected and options
    if len(value) != 2 or "options" not in value or "selected" not in value:
        keys = ", ".join(value.keys())
        return False, f"Enum parameter \"{name}\" must contain only \"selected\" and \"options\" properties, but it contains \"{keys}\""

    options = value.get("options")

    # options must be an object of type list
    if not isinstance(options, list):
        return False, f"Enum parameter \"{name}.options\" has invalid type. Expected \"list[str]\", got \"{type(options).__name__}\""

    # all elements of options list must be strings
    if not all(isinstance(element, str) for element in options):
        elementTypes = ", ".join({type(element).__name__ for element in options})
        return False, f"Elements of enum parameter \"{name}.options\" have invalid type. Expected \"list[str]\" got \"list[{elementTypes}]\""

    # options elements must not be empty strings
    if not all(element != "" for element in options):
        return False, f"Elements of enum parameter \"{name}.options\" must be non-empty strings."

    selected = value.get("selected")
    if selected is None and required:
        return False, f"Enum parameter \"{name}.selected\" has invalid type. Expected \"int\", got \"{type(selected).__name__}\""

    return True, None
