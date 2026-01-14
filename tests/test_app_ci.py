import importlib
import sys
import types
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))


def make_fake_streamlit(submitted=False, text_value=""):
    mod = types.ModuleType("streamlit")
    calls = []

    def set_page_config(*args, **kwargs):
        calls.append(("set_page_config", args, kwargs))

    def title(s):
        calls.append(("title", s))

    def markdown(s):
        calls.append(("markdown", s))

    class _FormCM:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    def form(key=None):
        calls.append(("form", key))
        return _FormCM()

    def text_area(label, height=None):
        calls.append(("text_area", label, height))
        return text_value

    def form_submit_button(label):
        calls.append(("form_submit_button", label))
        return submitted

    class _SpinnerCM:
        def __init__(self, msg):
            self.msg = msg

        def __enter__(self):
            calls.append(("spinner_enter", self.msg))
            return None

        def __exit__(self, exc_type, exc, tb):
            calls.append(("spinner_exit", self.msg))
            return False

    def spinner(msg):
        return _SpinnerCM(msg)

    def warning(msg):
        calls.append(("warning", msg))

    def error(msg):
        calls.append(("error", msg))

    def write(v):
        calls.append(("write", v))

    def success(msg):
        calls.append(("success", msg))

    def json(v):
        calls.append(("json", v))

    mod.set_page_config = set_page_config
    mod.title = title
    mod.markdown = markdown
    mod.form = form
    mod.text_area = text_area
    mod.form_submit_button = form_submit_button
    mod.spinner = spinner
    mod.warning = warning
    mod.error = error
    mod.write = write
    mod.success = success
    mod.json = json
    mod._calls = calls
    return mod


class MockRespSuccess:
    def raise_for_status(self):
        return None

    def json(self):
        return {"sentiment": "positive"}


class MockRespInvalidJSON:
    def raise_for_status(self):
        return None

    def json(self):
        raise ValueError()

    @property
    def text(self):
        return "not-json"


def make_fake_requests(response_obj=None, raise_exc=None):
    mod = types.ModuleType("requests")
    import requests as real_requests

    def post(url, json=None, timeout=None):
        if raise_exc:
            raise raise_exc
        return response_obj

    mod.post = post
    mod.exceptions = real_requests.exceptions
    return mod


def load_app_with_mocks(monkeypatch, fake_st, fake_requests):
    # ensure environment variable for API exists
    monkeypatch.setenv("API_URL", "http://fake")

    # replace modules before importing app
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    # remove app if already imported so import re-executes module top-level
    if "app" in sys.modules:
        del sys.modules["app"]

    return importlib.import_module("app")


def test_no_submit(monkeypatch):
    fake_st = make_fake_streamlit(submitted=False, text_value="hello")
    fake_req = make_fake_requests(response_obj=MockRespSuccess())
    load_app_with_mocks(monkeypatch, fake_st, fake_req)
    # when not submitted, we should not see success/error/json/warning related to submission
    names = [c[0] for c in fake_st._calls]
    assert "form_submit_button" in names
    assert "success" not in names
    assert "error" not in names


def test_submit_empty_text_shows_warning(monkeypatch):
    fake_st = make_fake_streamlit(submitted=True, text_value="   ")
    fake_req = make_fake_requests(response_obj=MockRespSuccess())
    load_app_with_mocks(monkeypatch, fake_st, fake_req)
    assert ("warning", "Veuillez entrer du texte avant d'envoyer.") in fake_st._calls


def test_submit_success_shows_json_and_success(monkeypatch):
    fake_st = make_fake_streamlit(submitted=True, text_value="Bonjour")
    fake_req = make_fake_requests(response_obj=MockRespSuccess())
    load_app_with_mocks(monkeypatch, fake_st, fake_req)
    assert ("success", "Réponse reçue") in fake_st._calls
    assert ("json", {"sentiment": "positive"}) in fake_st._calls


def test_api_invalid_json_shows_error_and_raw_text(monkeypatch):
    fake_st = make_fake_streamlit(submitted=True, text_value="Bonjour")
    fake_req = make_fake_requests(response_obj=MockRespInvalidJSON())
    load_app_with_mocks(monkeypatch, fake_st, fake_req)
    assert ("error", "Réponse invalide de l'API (JSON attendu).") in fake_st._calls
    assert ("write", "not-json") in fake_st._calls


def test_request_exception_shows_error(monkeypatch):
    fake_st = make_fake_streamlit(submitted=True, text_value="Bonjour")
    import requests as real_requests
    fake_req = make_fake_requests(raise_exc=real_requests.exceptions.Timeout("timeout"))
    load_app_with_mocks(monkeypatch, fake_st, fake_req)
    # expect an error call mentioning the exception message
    found = any(c[0] == "error" and "timeout" in str(c[1]) for c in fake_st._calls)
    assert found
