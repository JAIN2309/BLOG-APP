import os

class Config:
    SECRET_KEY = "3e2b45217bb64a8fb61725cc6277f858"  # Replace with a secure key
    SQLALCHEMY_DATABASE_URI = "sqlite:///blog.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "static/uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
