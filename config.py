import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "studyconnect_secret_key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        BASE_DIR,
        "instance",
        "studyconnect.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False