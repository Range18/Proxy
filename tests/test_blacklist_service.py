import pytest
from services.blacklist_service import BlacklistService


@pytest.fixture
def mock_blacklist(monkeypatch):
    def fake_exists(path):
        return True

    def fake_open(path, mode="r", *args, **kwargs):
        from io import StringIO
        return StringIO(
            '{"192.168.*": ["*"], "10.0.0.5": [80, 8080], "*.blocked.com": ["*"], "123.123.123.123": [443]}'
        )

    monkeypatch.setattr("os.path.exists", fake_exists)
    monkeypatch.setattr("builtins.open", fake_open)

    return {
        "192.168.*": ["*"],
        "10.0.0.5": [80, 8080],
        "*.blocked.com": ["*"],
        "123.123.123.123": [443],
    }


@pytest.fixture
def service(mock_blacklist):
    return BlacklistService()


def test_ip_matches_wildcard_port_any(service):
    """
    Проверяет, что IP, попадающий под паттерн, и имеющий '*' в списке портов — всегда заблокирован.
    """
    assert service.is_banned("192.168.1.5", 1234) is True


def test_exact_ip_specific_port_allowed(service):
    """
    Проверяет, что IP совпадает, но порт отсутствует в списке, поэтому доступ разрешён.
    """
    assert service.is_banned("10.0.0.5", 9999) is False


def test_exact_ip_specific_port_banned(service):
    """
    Проверяет, что IP совпадает и порт находится в списке — адрес заблокирован.
    """
    assert service.is_banned("10.0.0.5", 8080) is True


def test_domain_wildcard_blocked(service):
    """
    Проверяет, что домены с маской *.blocked.com всегда блокируются.
    """
    assert service.is_banned("sub.blocked.com", 80) is True


def test_ip_with_single_port_allowed_other(service):
    """
    Проверяет, что если у IP указан единственный порт, другие порты не блокируются.
    """
    assert service.is_banned("123.123.123.123", 80) is False


def test_ip_with_single_port_blocked(service):
    """
    Проверяет, что если у IP указан единственный порт, именно он блокируется.
    """
    assert service.is_banned("123.123.123.123", 443) is True


def test_no_match_returns_false(service):
    """
    Проверяет, что если IP не подходит ни под один шаблон — доступ разрешён.
    """
    assert service.is_banned("8.8.8.8", 53) is False
