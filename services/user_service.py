from datetime import date

from database import Session
from models.user_model import User


class UserService:
    def __init__(self):
        self.db = Session()

    def find_by_username(self, username: str) -> User:
        return self.db.query(User).filter_by(username=username).first()

    def update_user(
        self, user: User, ip: str | None = None, data_volume: int | None = None
    ) -> User:
        if ip is not None:
            user.ip = ip
        if data_volume is not None:
            user.data_volume = data_volume
        self.db.commit()
        return user

    def _reset_if_new_day(self, user: User):
        today = date.today()
        if user.last_reset_date != today:
            user.last_reset_date = today
            user.data_volume = 0
            self.db.commit()

    def check_data_overdraft(self, user: User, request_length: int) -> bool:
        if user.data_volume_limit is None:
            return False

        self._reset_if_new_day(user)

        if user.data_volume > user.data_volume_limit:
            return True

        if user.data_volume + request_length > user.data_volume_limit:
            self.update_user(user, data_volume=user.data_volume + request_length)
            return True

        self.update_user(user, data_volume=user.data_volume + request_length)
        return False
