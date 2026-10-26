import types

import openai

from api_client import call_model


class FakeAPIError(openai.APIError):
    """Stands in for a real API failure without building an HTTP request."""
    def __init__(self):
        Exception.__init__(self, "connection failed")


class FakeResponses:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise FakeAPIError()
        return types.SimpleNamespace(output_text="hello")


def fake_client(fail=False):
    return types.SimpleNamespace(responses=FakeResponses(fail))


def test_call_model_success():
    client = fake_client()
    result = call_model(client, "hi", model="test-model")
    assert result["ok"] is True
    assert result["text"] == "hello"
    assert client.responses.calls == [{"model": "test-model", "input": "hi"}]


def test_call_model_passes_instructions_only_when_given():
    client = fake_client()
    call_model(client, "hi", model="m", instructions="Be brief.")
    assert client.responses.calls[0]["instructions"] == "Be brief."


def test_call_model_failure_returns_dict():
    result = call_model(fake_client(fail=True), "hi")
    assert result["ok"] is False
    assert result["error"].startswith("FakeAPIError")
    assert result["elapsed_ms"] is not None