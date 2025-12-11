import base64
import pytest
from services.auth_service import AuthService
from models.user_model import User


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


@pytest.fixture
def auth_service(monkeypatch):
    service = AuthService()

    class FakeUserService:
        def __init__(self):
            self.last_updated = None
            self.user = None

        def find_by_username(self, username):
            return self.user

        def update_user(self, user, ip):
            self.last_updated = (user.username, ip)

    fake_service = FakeUserService()
    monkeypatch.setattr(service, "user_service", fake_service)
    return service, fake_service


def test_no_header(auth_service):
    """
    Проверяет, что при отсутствии заголовка proxy-authorization метод возвращает (None, False).
    """
    service, _ = auth_service
    req = FakeRequest(headers={})

    user, ok = service.check_auth(req, ip="127.0.0.1")

    assert user is None
    assert ok is False


def test_invalid_scheme(auth_service):
    """
    Проверяет, что при некорректной схеме авторизации возвращается (None, False).
    """
    service, _ = auth_service
    encoded = base64.b64encode(b"user:pass").decode()
    req = FakeRequest(headers={"proxy-authorization": f"Digest {encoded}"})

    user, ok = service.check_auth(req, ip="127.0.0.1")

    assert user is None
    assert ok is False


def test_user_not_found(auth_service):
    """
    Проверяет, что при неизвестном пользователе возвращается (None, False).
    """
    service, fake_service = auth_service
    fake_service.user = None

    encoded = base64.b64encode(b"ghost:pass").decode()
    req = FakeRequest(headers={"proxy-authorization": f"Basic {encoded}"})

    user, ok = service.check_auth(req, ip="127.0.0.1")

    assert user is None
    assert ok is False


def test_password_mismatch(auth_service):
    """
    Проверяет, что неправильный пароль приводит к (user, False).
    """
    service, fake_service = auth_service
    fake_service.user = User(username="john", password="correct")

    encoded = base64.b64encode(b"john:wrong").decode()
    req = FakeRequest(headers={"proxy-authorization": f"Basic {encoded}"})

    user, ok = service.check_auth(req, ip="127.0.0.1")

    assert user.username == "john"
    assert ok is False


def test_successful_auth(auth_service):
    """
    Проверяет успешную авторизацию: возвращается (user, True) и вызывается update_user.
    """
    service, fake_service = auth_service
    fake_service.user = User(username="john", password="secret")

    encoded = base64.b64encode(b"john:secret").decode()
    req = FakeRequest(headers={"proxy-authorization": f"Basic {encoded}"})

    user, ok = service.check_auth(req, ip="10.0.0.5")

    assert ok is True
    assert user.username == "john"
    assert fake_service.last_updated == ("john", "10.0.0.5")


def test_malformed_header(auth_service):
    """
    Проверяет, что некорректный base64 или формат header приводит к (None, False).
    """
    service, _ = auth_service
    req = FakeRequest(headers={"proxy-authorization": "Basic ???"})

    user, ok = service.check_auth(req, ip="127.0.0.1")

    assert user is None
    assert ok is False
