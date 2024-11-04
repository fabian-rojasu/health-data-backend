import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import models
from database import SessionLocal, engine
from schema import RegisterRequest

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los encabezados
)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):

    user = models.User(
        email=request.email,
        username=request.username,
        password=request.password,
        birthday=request.birthday,
        gender=request.gender,
    )
    # Fix: Convertir la fecha de nacimiento a un objeto datetime.date
    user.birthday = datetime.datetime.strptime(request.birthday, "%Y-%m-%d").date()

    db.add(user)
    try:
        db.commit()
        return {"message": "Usuario registrado correctamente"}
    except Exception as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al registrar el usuario")
