from fastapi import Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(self, status_code: int, error: str, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.error, "message": exc.message},
    )



# Common exceptions
class ConflictException(AppException):
    def __init__(self, message="Conflict occurred"):
        super().__init__(409, "CONFLICT", message)

class NotFoundException(AppException):
    def __init__(self, message="Resource not found"):
        super().__init__(404, "NOT_FOUND", message)

class UnauthorizedException(AppException):
    def __init__(self, message="Unauthorized"):
        super().__init__(401, "UNAUTHORIZED", message)

class ForbiddenException(AppException):
    def __init__(self, message="Access forbidden"):
        super().__init__(403, "FORBIDDEN", message)

class BadRequestException(AppException):
    def __init__(self, message="Bad request"):
        super().__init__(400, "BAD_REQUEST", message)

class PaymentException(AppException):
    def __init__(self, message="Payment failed"):
        super().__init__(402, "PAYMENT_FAILED", message)
