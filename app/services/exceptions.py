
class AppError(Exception):
    """Base class for expected application errors."""

    status_code = 500
    default_detail = "An application error occurred."

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


# Resources

class ResourceNotFoundError(AppError):
    status_code = 404
    default_detail = "The requested resource was not found."


class ResourceAlreadyExistsError(AppError):
    status_code = 409
    default_detail = "The resource already exists."


# Authentication and authorization

class InvalidCredentialsError(AppError):
    status_code = 401
    default_detail = "Invalid username or password."


class AuthenticationRequiredError(AppError):
    status_code = 401
    default_detail = "Authentication is required."


class PermissionDeniedError(AppError):
    status_code = 403
    default_detail = "You do not have permission to perform this action."


# Business rules

class BusinessRuleViolationError(AppError):
    status_code = 409
    default_detail = "The operation violates a business rule."


class InvalidStateTransitionError(BusinessRuleViolationError):
    default_detail = "The requested state transition is not allowed."


class TransactionCancelledError(InvalidStateTransitionError):
    default_detail = "A cancelled transaction cannot be modified."


class GoalAlreadyEndedError(InvalidStateTransitionError):
    default_detail = "This operation is not allowed because the goal has ended."