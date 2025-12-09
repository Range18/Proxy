import base64

from database import Session
from models.http_request import HttpRequest
from models.user_model import User
from services.user_service import UserService


class AuthService:
    def __init__(self):
        self.user_service = UserService()

    def check_auth(self, request: HttpRequest, ip: str) -> (User, bool):
        header = request.headers.get("proxy-authorization")
        if not header:
            return None, False

        try:
            scheme, data = header.split(" ", 1)
            if scheme.lower() != "basic":
                return None, False

            decoded = base64.b64decode(data).decode("utf-8")
            username, password = decoded.split(":", 1)

            user = self.user_service.find_by_username(username)
            if user is None:
                print(f"User {username} not found")
                return None, False

            ok = user.password == password
            if ok:
                self.user_service.update_user(user, ip=ip)
            return user, ok

        except Exception as e:
            print("Auth error:", e)
            return None, False
