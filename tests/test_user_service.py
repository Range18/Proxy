import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta

from services.user_service import UserService


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def user():
    u = MagicMock()
    u.username = "test"
    u.ip = None
    u.data_volume = 0
    u.data_volume_limit = 100
    u.last_reset_date = date.today()
    return u


@pytest.fixture
def service(mock_session):
    s = UserService()
    s.db = mock_session
    return s


def test_find_by_username(service, mock_session):
    """
    Проверяет, что find_by_username вызывает запрос к БД и возвращает пользователя.
    """
    expected_user = MagicMock()
    query_mock = MagicMock()
    mock_session.query.return_value = query_mock
    query_mock.filter_by.return_value.first.return_value = expected_user

    result = service.find_by_username("test")

    mock_session.query.assert_called_once()
    query_mock.filter_by.assert_called_once_with(username="test")
    assert result == expected_user


def test_update_user_updates_ip_and_volume(service, mock_session, user):
    """
    Проверяет, что update_user обновляет ip и data_volume, затем вызывает commit.
    """
    updated = service.update_user(user, ip="1.2.3.4", data_volume=42)

    assert updated.ip == "1.2.3.4"
    assert updated.data_volume == 42
    mock_session.commit.assert_called_once()


def test_reset_if_new_day_resets_volume(service, mock_session, user):
    """
    Проверяет, что при наступлении нового дня сбрасывается объём и обновляется last_reset_date.
    """
    user.last_reset_date = date.today() - timedelta(days=1)

    service._reset_if_new_day(user)

    assert user.last_reset_date == date.today()
    assert user.data_volume == 0
    mock_session.commit.assert_called_once()


def test_reset_if_new_day_same_day_no_change(service, mock_session, user):
    """
    Проверяет, что в тот же день сброс не происходит.
    """
    user.last_reset_date = date.today()

    service._reset_if_new_day(user)

    mock_session.commit.assert_not_called()


def test_check_data_overdraft_no_limit(service, user):
    """
    Проверяет, что при отсутствии лимита всегда возвращается False.
    """
    user.data_volume_limit = None

    result = service.check_data_overdraft(user, 50)

    assert result is False


def test_check_data_overdraft_over_existing_limit(service, user):
    """
    Проверяет, что если текущий объем уже превышает лимит, возвращается True.
    """
    user.data_volume = 150
    user.data_volume_limit = 100

    result = service.check_data_overdraft(user, 10)

    assert result is True


def test_check_data_overdraft_exceeds_limit_after_request(service, mock_session, user):
    """
    Проверяет, что если сумма объема и запроса превышает лимит, update_user вызывается и возвращается True.
    """
    user.data_volume = 90
    user.data_volume_limit = 100

    result = service.check_data_overdraft(user, 20)

    assert result is True
    service.db.commit.assert_called_once()  # commit внутри update_user


def test_check_data_overdraft_within_limit(service, mock_session, user):
    """
    Проверяет, что если лимит не превышен, данные обновляются и возвращается False.
    """
    user.data_volume = 40
    user.data_volume_limit = 100

    result = service.check_data_overdraft(user, 30)

    assert result is False
    service.db.commit.assert_called_once()  # commit внутри update_user
