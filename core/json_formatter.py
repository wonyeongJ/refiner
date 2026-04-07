import json

def format_json(raw_json: str) -> str:
    """
    Parses a raw JSON string and formats it with 4 spaces indentation.
    If parsing fails, raises an exception to be handled by the caller.
    """
    if not raw_json.strip():
        return ""
        
    try:
        # Load the JSON data
        parsed = json.loads(raw_json)
        # Dump it back with formatting
        return json.dumps(parsed, indent=4, ensure_ascii=False)
    except json.JSONDecodeError as e:
        raise ValueError(f"유효하지 않은 JSON 형태입니다.\n상세 오류: {str(e)}")
