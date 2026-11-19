import pytest

from assistant.output_validator import validate_response


@pytest.mark.parametrize(
    "response",
    [
        "The business review is complete.",
        "The current context is available.",
        "BUSINESS and CONTEXT",
    ],
)
def test_validate_response_suppresses_restricted_words(response):
    valid, result = validate_response(response)

    assert valid is False
    assert result == (
        "The generated response contained restricted wording "
        "and was suppressed."
    )


def test_validate_response_allows_words_that_only_contain_restricted_terms():
    response = "The businesslike approach is contextual."

    assert validate_response(response) == (True, response)
