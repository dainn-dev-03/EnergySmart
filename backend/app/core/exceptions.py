"""Application exceptions. Services raise these; handlers turn them into the error envelope."""

from collections.abc import Mapping
from typing import ClassVar

from fastapi import status

from app.schemas.common import ErrorDetail


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    default_message: str = "Đã xảy ra lỗi hệ thống"
    headers: ClassVar[Mapping[str, str] | None] = None

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        self.message = message or self.default_message
        if code is not None:
            self.code = code
        self.details = details
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"
    default_message = "Yêu cầu không hợp lệ"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"
    default_message = "Chưa đăng nhập hoặc phiên đăng nhập đã hết hạn"
    headers: ClassVar[Mapping[str, str] | None] = {"WWW-Authenticate": "Bearer"}


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"
    default_message = "Bạn không có quyền thực hiện thao tác này"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    default_message = "Không tìm thấy dữ liệu"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"
    default_message = "Dữ liệu bị trùng hoặc đang được sử dụng"

    @classmethod
    def for_field(cls, field: str, message: str) -> "ConflictError":
        return cls(message, details=[ErrorDetail(field=field, message=message)])


class InvalidInputError(AppError):
    """Input passed schema validation but is invalid against the data (e.g. unknown parent id)."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "VALIDATION_ERROR"
    default_message = "Dữ liệu không hợp lệ"

    @classmethod
    def for_field(cls, field: str, message: str) -> "InvalidInputError":
        return cls(details=[ErrorDetail(field=field, message=message)])


class BusinessRuleError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "BUSINESS_RULE_VIOLATION"
    default_message = "Thao tác vi phạm quy tắc nghiệp vụ"


class ServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "SERVICE_UNAVAILABLE"
    default_message = "Dịch vụ tạm thời không khả dụng"
