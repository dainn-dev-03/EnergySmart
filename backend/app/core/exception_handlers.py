"""Translate every error into the `{"success": false, "message", "error": {"code"}}` envelope."""

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.schemas.common import ErrorDetail, ErrorInfo, ErrorResponse

logger = logging.getLogger(__name__)

_HTTP_ERRORS: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "Yêu cầu không hợp lệ"),
    401: ("UNAUTHORIZED", "Chưa đăng nhập hoặc phiên đăng nhập đã hết hạn"),
    403: ("FORBIDDEN", "Bạn không có quyền thực hiện thao tác này"),
    404: ("NOT_FOUND", "Không tìm thấy đường dẫn"),
    405: ("METHOD_NOT_ALLOWED", "Phương thức không được hỗ trợ"),
    409: ("CONFLICT", "Dữ liệu bị trùng hoặc đang được sử dụng"),
    429: ("TOO_MANY_REQUESTS", "Quá nhiều yêu cầu, vui lòng thử lại sau"),
}

_VALIDATION_MESSAGES: dict[str, str] = {
    "missing": "Trường này là bắt buộc",
    "string_too_short": "Phải có ít nhất {min_length} ký tự",
    "string_too_long": "Không được vượt quá {max_length} ký tự",
    "greater_than": "Phải lớn hơn {gt}",
    "greater_than_equal": "Phải lớn hơn hoặc bằng {ge}",
    "less_than": "Phải nhỏ hơn {lt}",
    "less_than_equal": "Phải nhỏ hơn hoặc bằng {le}",
    "int_parsing": "Phải là số nguyên",
    "int_type": "Phải là số nguyên",
    "int_from_float": "Phải là số nguyên",
    "float_parsing": "Phải là số",
    "float_type": "Phải là số",
    "decimal_parsing": "Phải là số",
    "decimal_type": "Phải là số",
    "decimal_max_digits": "Tối đa {max_digits} chữ số",
    "decimal_max_places": "Tối đa {decimal_places} chữ số thập phân",
    "decimal_whole_digits": "Phần nguyên tối đa {whole_digits} chữ số",
    "string_pattern_mismatch": "Chỉ gồm chữ cái không dấu, chữ số và các ký tự - _ .",
    "bool_parsing": "Phải là true hoặc false",
    "string_type": "Phải là chuỗi ký tự",
    "date_parsing": "Ngày không hợp lệ (định dạng YYYY-MM-DD)",
    "date_from_datetime_parsing": "Ngày không hợp lệ (định dạng YYYY-MM-DD)",
    "datetime_parsing": "Thời gian không hợp lệ (định dạng ISO 8601)",
    "datetime_from_date_parsing": "Thời gian không hợp lệ (định dạng ISO 8601)",
    "enum": "Giá trị phải là một trong: {expected}",
    "literal_error": "Giá trị phải là một trong: {expected}",
    "json_invalid": "JSON không hợp lệ",
}

_LOCATION_PREFIXES = {"body", "query", "path", "header", "cookie"}


def _error_response(
    status_code: int,
    message: str,
    code: str,
    details: list[ErrorDetail] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(message=message, error=ErrorInfo(code=code, details=details))
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(exclude_none=True),
        headers=dict(headers) if headers else None,
    )


def _field_path(location: Sequence[Any]) -> str | None:
    parts = [str(part) for part in location]
    if parts and parts[0] in _LOCATION_PREFIXES:
        parts = parts[1:]
    return ".".join(parts) or None


def _translate_validation_error(error: Mapping[str, Any]) -> str:
    template = _VALIDATION_MESSAGES.get(str(error.get("type")))
    if template is None:
        return str(error.get("msg", "Giá trị không hợp lệ")).removeprefix("Value error, ")
    try:
        return template.format(**(error.get("ctx") or {}))
    except (KeyError, IndexError):
        return template


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.message, exc.code, exc.details, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            ErrorDetail(
                field=_field_path(error.get("loc", ())),
                message=_translate_validation_error(error),
            )
            for error in exc.errors()
        ]
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Dữ liệu không hợp lệ",
            "VALIDATION_ERROR",
            details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, message = _HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", str(exc.detail)))
        return _error_response(exc.status_code, message, code, headers=exc.headers)

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Integrity error: %s", exc.orig)
        return _error_response(
            status.HTTP_409_CONFLICT,
            "Dữ liệu vi phạm ràng buộc (bị trùng hoặc đang được tham chiếu)",
            "CONFLICT",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Đã xảy ra lỗi hệ thống",
            "INTERNAL_ERROR",
        )
