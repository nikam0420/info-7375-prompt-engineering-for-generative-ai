"""UTF-8 JSON decoding reused from Agent 1 watcher/postings.py."""
import json


class PostingValidationError(ValueError):
    """The response or a posting in it is malformed."""


def decode_json_bytes(raw: bytes):
    if not isinstance(raw, (bytes, bytearray)):
        raise PostingValidationError("response body must be bytes")
    try:
        text = bytes(raw).decode("utf-8")
    except UnicodeDecodeError as err:
        raise PostingValidationError(f"response is not valid UTF-8: {err}") from err
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise PostingValidationError(f"response is not valid JSON: {err}") from err
