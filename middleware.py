import time
import traceback
import uuid
import json
from typing import Callable, Awaitable, Dict, Any

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from config import get_settings
from utils.responses import error_payload, detect_lang  # type: ignore
from i18n.messages import is_supported_lang, normalize_lang
from starlette.middleware.base import RequestResponseEndpoint

settings = get_settings()
from starlette.responses import Response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.time()
        path = request.url.path
        method = request.method
        request_id = request.headers.get(settings.request_id_header)
        if not request_id:
            request_id = uuid.uuid4().hex
        # Attach to state so handlers can reuse
        request.state.request_id = request_id
        try:
            response = await call_next(request)
            duration = (time.time() - start) * 1000
            log_record: Dict[str, Any] = {
                "level": "INFO",
                "msg": "request",
                "method": method,
                "path": path,
                "status": response.status_code,
                "duration_ms": round(duration, 2),
                "request_id": request_id,
            }
            response.headers[settings.request_id_header] = request_id
            print(json.dumps(log_record))
            return response
        except Exception:
            duration = (time.time() - start) * 1000
            error_record: Dict[str, Any] = {
                "level": "ERROR",
                "msg": "unhandled_exception",
                "method": method,
                "path": path,
                "duration_ms": round(duration, 2),
                "request_id": request_id,
                "trace": traceback.format_exc(),
            }
            print(json.dumps(error_record))
            raise


class LanguagePrefixMiddleware(BaseHTTPMiddleware):
    """Middleware untuk mendukung prefix bahasa di path: /en/..., /id/..., /ja/... dll.

    Mekanisme:
    - Cek segmen pertama path
    - Jika bahasa didukung, simpan di request.state.lang
    - Strip segmen bahasa sebelum diteruskan ke router FastAPI
    - Jika hanya prefix bahasa (misal '/en') redirect ke '/en/' agar konsisten
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:  # type: ignore[override]
        original_path = request.scope.get("path", "")
        if not isinstance(original_path, str) or len(original_path) < 4:  # minimal '/en'
            return await call_next(request)
        # Pisah segmen
        # path selalu diawali '/', jadi split akan hasilkan pertama kosong
        segments = original_path.split('/')
        # ['', 'en', 'login'] -> kandidat bahasa di index 1
        candidate = segments[1] if len(segments) > 1 else None
        if candidate and is_supported_lang(candidate.lower()):
            # Normalisasi
            lang_norm = normalize_lang(candidate.lower())
            request.state.lang = lang_norm
            # Bangun ulang path tanpa segmen bahasa
            remainder_segments = segments[2:]  # sisakan setelah kode bahasa
            new_path = '/' + '/'.join([s for s in remainder_segments if s])
            if new_path == '/':
                # jika user akses '/en' atau '/en/' arahkan ke root tapi lang terset
                request.scope['path'] = '/'  # root
            else:
                request.scope['path'] = new_path
        return await call_next(request)


async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    request_id = getattr(request.state, "request_id", None)
    lang = detect_lang(request)
    detail = exc.detail
    detail_key_map = {
        "Not authenticated": "not_authenticated",
        "Tidak bisa validasi token": "not_authenticated",
        "NIP atau password salah": "invalid_credentials",
        "Validation error": "validation_error",
        "Data tidak valid": "validation_error",
    }
    key = detail_key_map.get(str(detail))

    body: Dict[str, Any]  # anotasi eksplisit agar Pylance tahu tipe
    if key:
        body = error_payload(exc.status_code, key, lang)
    else:
        body = {
            "success": False,
            "code": exc.status_code,
            "message": str(detail),
        }
    if request_id:
        body["request_id"] = request_id
    resp = JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)
    if request_id:
        resp.headers[settings.request_id_header] = request_id
    return resp


async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    lang = detect_lang(request)
    body = error_payload(500, "internal_error", lang)
    if request_id:
        body["request_id"] = request_id
    resp = JSONResponse(status_code=500, content=body)
    if request_id:
        resp.headers[settings.request_id_header] = request_id
    return resp


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    lang = detect_lang(request)
    body = error_payload(422, "validation_error", lang, extra={"details": exc.errors()})
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=422, content=body)


def add_exception_handlers(app: FastAPI) -> None:
    # Explicit registration avoids Pylance unused-function warnings
    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
