from datetime import date
from sqlalchemy import Column, Integer, String, Date

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    ip = Column(String, nullable=True)

    data_volume = Column(Integer, nullable=False, default=0)
    data_volume_limit = Column(Integer, nullable=True)
    last_reset_date = Column(Date, default=date.today)
