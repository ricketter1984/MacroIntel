import re


def parse_condition(query_str):
    """
    Parse a string condition like 'fear < 30' or 'vix > 40' into a structured dictionary.
    Returns: dict with keys: type, operator, value
    Raises ValueError for invalid conditions.
    """
    pattern = r"\s*(fear|vix)\s*([<>]=?|==|!=)\s*(\d+(?:\.\d+)?)\s*"
    match = re.fullmatch(pattern, query_str.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid condition format: '{query_str}'")
    cond_type, operator, value = match.groups()
    try:
        value = float(value) if '.' in value else int(value)
    except Exception:
        raise ValueError(f"Invalid numeric value in condition: '{query_str}'")
    return {
        "type": cond_type.lower(),
        "operator": operator,
        "value": value
    }

# Example usage
if __name__ == "__main__":
    test_cases = [
        "fear < 30",
        "vix > 40",
        "fear >= 50",
        "vix != 20",
        "fear == 10",
        "invalid condition"
    ]
    for q in test_cases:
        try:
            print(f"{q} -> {parse_condition(q)}")
        except Exception as e:
            print(f"{q} -> Error: {e}") 