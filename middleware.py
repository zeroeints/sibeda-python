# pyright: reportGeneralTypeIssues=false, reportUnknownMemberType=false
# type: ignore
import time
import uuid
import json
from typing import Callable, Awaitable, Dict, Any, cast, Mapping

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import RequestResponseEndpoint

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from config import get_settings
from utils.responses import error_payload, detect_lang
from i18n.messages import is_supported_lang, normalize_lang

settings = get_settings()

# Konfigurasi Rich Console
custom_theme = Theme({
    "info": "green",
    "warning": "yellow",
    "error": "bold red",
    "method": "bold cyan",
    "path": "bold white",
})
console = Console(theme=custom_theme)


def _as_bytes(buf: bytes | bytearray | memoryview) -> bytes:
    """Normalize various buffer types into bytes with clear type narrowing for Pylance."""
    if isinstance(buf, bytes):
        return buf
    if isinstance(buf, bytearray):
        return bytes(buf)
    # memoryview
    return buf.tobytes()


def _to_safe_json(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable objects (like bytes) into safe forms.
    - bytes/bytearray/memoryview -> try utf-8 decode, else base64 string
    - Exception objects -> convert to string
    - dict/list/tuple/set -> recurse
    """
    import base64
    if isinstance(obj, (bytes, bytearray, memoryview)):
        buf = _as_bytes(cast(bytes | bytearray | memoryview, obj))
        try:
            return buf.decode("utf-8")
        except Exception:
            return base64.b64encode(buf).decode("ascii")
    # Handle Exception objects (ValueError, etc.)
    if isinstance(obj, Exception):
        return str(obj)
    if isinstance(obj, dict):
        d = cast(Mapping[Any, Any], obj)
        return {k: _to_safe_json(v) for k, v in d.items()}
    # Handle common sequence types explicitly to aid type checkers
    if isinstance(obj, list):
        lst = cast(list[Any], obj)
        return [_to_safe_json(v) for v in lst]
    if isinstance(obj, tuple):
        tpl = cast(tuple[Any, ...], obj)
        return [_to_safe_json(v) for v in tpl]
    if isinstance(obj, set):
        st = cast(set[Any], obj)
        return [_to_safe_json(v) for v in st]
    return obj

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
        request_id = request.headers.get(settings.request_id_header) or uuid.uuid4().hex
        request.state.request_id = request_id

        # Clone request body
        body_bytes = await request.body()
        
        # Override receive
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive

        try:
            response = await call_next(request)
            duration = (time.time() - start) * 1000

            # Tentukan warna berdasarkan status code
            status_color = "green"
            if response.status_code >= 400: status_color = "yellow"
            if response.status_code >= 500: status_color = "red"

            # Log singkat satu baris yang jelas
            log_message = (
                f"[method]{method}[/method] "
                f"[path]{path}[/path] "
                f"[{status_color}]{response.status_code}[/{status_color}] "
                f"- [bold]{duration:.2f}ms[/bold]"
            )
            console.print(log_message)

            # Jika Debug Mode ON atau terjadi Error, tampilkan detail
            if settings.debug or response.status_code >= 400:
                self._print_debug_details(request, body_bytes, response, request_id, status_color)

            response.headers[settings.request_id_header] = request_id
            return response

        except Exception as e:
            duration = (time.time() - start) * 1000
            console.print(f"[error]UNHANDLED EXCEPTION[/error] in {method} {path} - {duration:.2f}ms")
            console.print_exception(show_locals=False) # Tampilkan traceback yang cantik
            raise e

    def _print_debug_details(self, request, body_bytes, response, request_id, color):
        """Helper untuk mencetak detail body/response saat debug"""
        try:
            # Request Body
            req_body_str = ""
            if body_bytes:
                try:
                    req_json = json.loads(body_bytes)
                    req_body_str = json.dumps(req_json, indent=2)
                except:
                    req_body_str = body_bytes.decode("utf-8", errors="ignore")

            # Panel konten
            content = f"[bold]Request ID:[/bold] {request_id}\n"
            if request.query_params:
                content += f"[bold]Query:[/bold] {dict(request.query_params)}\n"
            if req_body_str:
                content += f"[bold]Request Body:[/bold]\n{req_body_str}\n"
            
            # Response Body (Hati-hati jika response streaming/besar)
            if hasattr(response, "body"):
                try:
                    res_body = response.body.decode("utf-8", errors="ignore")
                    # Coba format JSON jika memungkinkan
                    try:
                        res_json = json.loads(res_body)
                        res_body = json.dumps(res_json, indent=2)
                    except:
                        pass
                    content += f"[bold]Response Body:[/bold]\n{res_body}"
                except:
                    pass

            console.print(Panel(content, title="Details", border_style=color, expand=False))
        except Exception:
            pass # Jangan sampai logging bikin error aplikasi


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
    # Sanitize pydantic v2 errors which may include non-serializable values (e.g., bytes in 'input')
    safe_errors = _to_safe_json(exc.errors())
    # Keep both 'details' (project convention) and 'detail' (FastAPI default) for compatibility
    body = error_payload(422, "validation_error", lang, extra={"details": safe_errors, "detail": safe_errors})
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=422, content=body)


def add_exception_handlers(app: FastAPI) -> None:
    # Explicit registration avoids Pylance unused-function warnings
    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
