import pytest

from junior_apogee_app.errors import AgentError, ConfigurationError, EvaluationError


def test_exceptions_inherit():
    assert issubclass(ConfigurationError, Exception)
    assert issubclass(EvaluationError, Exception)
    assert issubclass(AgentError, Exception)


def test_raise_evaluation_error():
    with pytest.raises(EvaluationError):
        raise EvaluationError("oops")
