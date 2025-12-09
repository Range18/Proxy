from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

engine = create_engine("sqlite:///db.sqlite", echo=True)

Session = sessionmaker(bind=engine)
