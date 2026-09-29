"""Safe, classified failures shared by the client and MCP boundary."""


class MissingCredentialsError(RuntimeError):
    def __init__(self, variables: tuple[str, ...]):
        self.variables = variables
        names = " and ".join(variables)
        super().__init__(f"Missing {names}. Run: rocketmatter-mcp-setup")


class AuthenticationError(RuntimeError):
    pass


class VendorHTTPError(RuntimeError):
    def __init__(self, status: int, reason: str, retry_after: str | None = None):
        self.status = status
        self.reason = reason
        self.retry_after = retry_after
        super().__init__(f"HTTP {status}: {reason}")


class ArgumentValidationError(RuntimeError, ValueError):
    def __init__(self, argument: str, expected: str):
        self.argument = argument
        self.expected = expected
        super().__init__(f"{argument} must be {expected}")


class NotFoundError(RuntimeError):
    pass


class CapabilityUnavailableError(RuntimeError):
    pass
