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
