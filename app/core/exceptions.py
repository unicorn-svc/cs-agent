"""Custom exceptions for the application."""


class AgentException(Exception):
    """Base exception for the agent."""

    pass


class ValidationError(AgentException):
    """Validation error."""

    pass


class LLMError(AgentException):
    """LLM service error."""

    pass


class FAQSearchError(AgentException):
    """FAQ search service error."""

    pass


class DatabaseError(AgentException):
    """Database operation error."""

    pass


class ExternalSystemError(AgentException):
    """External system integration error."""

    pass


class TimeoutError(AgentException):
    """Operation timeout error."""

    pass
