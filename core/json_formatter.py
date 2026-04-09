import json


def format_json(raw_json: str) -> str:
    """
    Parses a raw JSON string and formats it with 4 spaces indentation.
    Supports leading/trailing plain text around the first JSON object/array.
    """
    if not raw_json.strip():
        return ""

    try:
        stripped = raw_json.strip()
        start = 0

        # If plain text exists before JSON, keep it and format only JSON payload.
        if stripped and stripped[0] not in ("{", "["):
            obj_pos = stripped.find("{")
            arr_pos = stripped.find("[")
            candidates = [p for p in (obj_pos, arr_pos) if p >= 0]
            if not candidates:
                raise json.JSONDecodeError("No JSON object/array start found", stripped, 0)
            start = min(candidates)

        prefix = stripped[:start].rstrip()
        payload = stripped[start:]

        decoder = json.JSONDecoder()
        parsed, end_idx = decoder.raw_decode(payload)
        formatted = json.dumps(parsed, indent=4, ensure_ascii=False)

        suffix = payload[end_idx:].strip()

        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(formatted)
        if suffix:
            parts.append(suffix)
        return "\n".join(parts)

    except json.JSONDecodeError as e:
        raise ValueError(f"유효하지 않은 JSON 형태입니다.\n상세 오류: {str(e)}")
