from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import Request
from i18n.messages import get_message, normalize_lang

# Helper untuk menentukan bahasa dari request
LANG_HEADER = "X-Lang"


def detect_lang(request: Request, explicit_lang: str | None = None) -> str:
    if explicit_lang:
        return normalize_lang(explicit_lang)
    # prioritas: query ?lang= > header X-Lang > token claim (request.state.lang) > default
    if request.query_params.get("lang"):
        return normalize_lang(request.query_params.get("lang"))
    if request.headers.get(LANG_HEADER):
        return normalize_lang(request.headers.get(LANG_HEADER))
    state_lang = getattr(request.state, "lang", None)
    return normalize_lang(state_lang)


def success_payload(data: Any = None, message_key: str | None = None, lang: str | None = None) -> Dict[str, Any]:
    msg = get_message(message_key, lang) if message_key else None
    return {"success": True, "data": data, "message": msg}


def error_payload(code: int, message_key: str, lang: str | None = None, *, detail_override: str | None = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    msg = detail_override or get_message(message_key, lang)
    body: Dict[str, Any] = {"success": False, "code": code, "message": msg}
    if extra:
        body.update(extra)
    return body
