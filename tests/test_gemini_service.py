from services import gemini


def test_build_gemini_client_returns_none_when_sdk_is_unavailable(monkeypatch):
    monkeypatch.setattr(gemini, "_import_google_sdk", lambda: None)

    client = gemini._build_gemini_client("test-key")

    assert client is None
