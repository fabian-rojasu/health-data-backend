from fastapi import FastAPI
from database import engine, Base
from models import User
from database import SessionLocal, engine, Base
from datetime import date
import models

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/")
def hello_world():
    return {"message": "Hello World"}

