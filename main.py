import csv
from datetime import datetime, timedelta
from io import StringIO
from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from pydantic import BaseModel, EmailStr
import models
from database import SessionLocal, engine
from schema import LoginRequest, RegisterRequest
from typing import Literal

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
    user.birthday = datetime.strptime(request.birthday, "%Y-%m-%d").date()

    db.add(user)
    try:
        db.commit()
        return {"message": "Usuario registrado correctamente"}
    except Exception as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al registrar el usuario")


@app.post("/login")
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if user is None:
        print(user)
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.password != req.password:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    return {"message": "Inicio de sesión correcto", "ok": True, "userId": user.id}


@app.get("/dashboard/general/{user_id}")
def get_general_dashboard(user_id: int, db: Session = Depends(get_db)):

    latest_weight = (
        db.query(models.Weight)
        .filter(models.Weight.user_id == user_id)
        .order_by(models.Weight.date.desc())
        .first()
    )

    latest_height = (
        db.query(models.Height)
        .filter(models.Height.user_id == user_id)
        .order_by(models.Height.date.desc())
        .first()
    )

    latest_composition = (
        db.query(models.BodyComposition)
        .filter(models.BodyComposition.user_id == user_id)
        .order_by(models.BodyComposition.date.desc())
        .first()
    )

    # Get latest body fat percentage
    latest_fat_percentage = (
        db.query(models.BodyFatPercentage)
        .filter(models.BodyFatPercentage.user_id == user_id)
        .order_by(models.BodyFatPercentage.date.desc())
        .first()
    )

    latest_water = (
        db.query(models.WaterConsumption)
        .filter(models.WaterConsumption.user_id == user_id)
        .order_by(models.WaterConsumption.date.desc())
        .first()
    )

    latest_steps = (
        db.query(models.DailyStep)
        .filter(models.DailyStep.user_id == user_id)
        .order_by(models.DailyStep.date.desc())
        .first()
    )

    # Modificar la consulta de ejercicios para obtener solo los de la última fecha
    latest_exercise_date = (
        db.query(func.max(models.Exercise.date))
        .filter(models.Exercise.user_id == user_id)
        .scalar()
    )

    latest_exercises = (
        db.query(models.Exercise)
        .filter(
            models.Exercise.user_id == user_id,
            models.Exercise.date == latest_exercise_date
        )
        .all()
    ) if latest_exercise_date else []

    if not latest_weight or not latest_height:
        return {
            "current_weight": None,
            "current_height": None,
            "body_composition": {
                "fat": None,
                "muscle": None,
                "water": None,
            },
            "bmi": None,
            "body_fat_percentage": None,
            "water_glasses": 0,
            "steps": 0,
            "exercises": [],
        }

    bmi = latest_weight.weight / ((latest_height.height / 100) ** 2)

    return {
        "current_weight": latest_weight.weight,
        "current_height": latest_height.height,
        "body_composition": {
            "fat": latest_composition.fat if latest_composition else None,
            "muscle": latest_composition.muscle if latest_composition else None,
            "water": latest_composition.water if latest_composition else None,
        },
        "bmi": round(bmi, 2),
        "body_fat_percentage": (
            latest_fat_percentage.fat_percentage if latest_fat_percentage else None
        ),  # in %
        "water_glasses": latest_water.water_amount if latest_water else 0,
        "steps": latest_steps.steps_amount if latest_steps else 0,
        "exercises": (
            [
                {
                    "name": exercise.exercise_name,
                    "duration": exercise.duration,
                }
                for exercise in latest_exercises
            ]
            if latest_exercises
            else []
        ),
    }


@app.post("/import-data")
async def import_data(
    user_id: int = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        content = await file.read()
        csv_text = content.decode("utf-8")
        csv_reader = csv.reader(StringIO(csv_text))
        next(csv_reader)  # Skip header row

        if file_type == "weight":
            for row in csv_reader:
                date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                weight = float(row[1])

                weight_record = models.Weight(user_id=user_id, date=date, weight=weight)
                db.merge(weight_record)

        elif file_type == "height":
            for row in csv_reader:

                date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                print(date)
                height = float(row[1])
                print(height)
                height_record = models.Height(user_id=user_id, date=date, height=height)
                db.merge(height_record)

        elif file_type == "body_composition":
            for row in csv_reader:
                date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                fat = float(row[1])
                muscle = float(row[2])
                water = float(row[3])

                composition_record = models.BodyComposition(
                    user_id=user_id, date=date, fat=fat, muscle=muscle, water=water
                )
                db.merge(composition_record)

        elif file_type == "body_fat_percentage":
            for row in csv_reader:
                date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                fat_percentage = float(row[1])

                fat_record = models.BodyFatPercentage(
                    user_id=user_id, date=date, fat_percentage=fat_percentage
                )
                db.merge(fat_record)

        elif file_type == "water":
            for row in csv_reader:
                date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                water_amount = int(row[1])

                water_record = models.WaterConsumption(
                    user_id=user_id, date=date, water_amount=water_amount
                )
                db.merge(water_record)

        elif file_type == "steps":
            for row in csv_reader:
                date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                steps = int(row[1])

                steps_record = models.DailyStep(
                    user_id=user_id, date=date, steps_amount=steps
                )
                db.merge(steps_record)

        elif file_type == "exercises":
            for row in csv_reader:
                date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                exercise_name = row[1]
                duration = int(row[2])

                exercise_record = models.Exercise(
                    user_id=user_id,
                    date=date,
                    exercise_name=exercise_name,
                    duration=duration,
                )
                db.merge(exercise_record)

        else:
            raise HTTPException(status_code=400, detail="Invalid file type")

        db.commit()
        return {"message": "Data imported successfully"}

    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=400, detail=str(e))



@app.get("/profile/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "email": user.email,
        "username": user.username,
        "password": user.password,
        "birthday": user.birthday,
        "gender": user.gender,
    }

@app.put("/profile/{user_id}")
def update_user_profile(user_id: int, profile_data:RegisterRequest , db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Actualiza los campos del usuario
    user.email = profile_data.email
    user.username = profile_data.username
    user.password = profile_data.password
    user.birthday = profile_data.birthday
    user.gender = profile_data.gender

    user.birthday = datetime.strptime(profile_data.birthday, "%Y-%m-%d").date()
    db.commit()
    return {"message": "User profile updated successfully"}

TimeRange = Literal["1w", "1m", "3m", "6m", "1y"]

@app.get("/dashboard/historical/{user_id}")
def get_historical_data(
    user_id: int, 
    time_range: TimeRange,
    metric_type: Literal["weight", "muscle", "fat", "water", "steps", "exercise"],
    db: Session = Depends(get_db)
):
    end_date = datetime.now()
    range_mapping = {
        "1w": timedelta(days=7),
        "1m": timedelta(days=30),
        "3m": timedelta(days=90),
        "6m": timedelta(days=180),
        "1y": timedelta(days=365),
    }
    start_date = end_date - range_mapping[time_range]
    
    # Define el formato de agrupación según el rango de tiempo
    date_format = {
        "1w": '%Y-%m-%d',           # Días
        "1m": '%Y-%W',              # Semanas
        "3m": '%Y-%W',              # Semanas
        "6m": '%Y-%m',              # Meses
        "1y": '%Y-%m',              # Meses
    }[time_range]

    if metric_type == "weight":
        date_group = func.strftime(date_format, models.Weight.date)
        query = (
            db.query(
                date_group.label('date'),
                func.avg(models.Weight.weight).label('value')
            )
            .filter(
                and_(
                    models.Weight.user_id == user_id,
                    models.Weight.date >= start_date,
                    models.Weight.date <= end_date
                )
            )
            .group_by(date_group)
            .order_by('date')
        )
    
    elif metric_type == "muscle":
        date_group = func.strftime(date_format, models.BodyComposition.date)
        query = (
            db.query(
                date_group.label('date'),
                func.avg(models.BodyComposition.muscle).label('value')
            )
            .filter(
                and_(
                    models.BodyComposition.user_id == user_id,
                    models.BodyComposition.date >= start_date,
                    models.BodyComposition.date <= end_date
                )
            )
            .group_by(date_group)
            .order_by('date')
        )
    
    elif metric_type == "fat":
        date_group = func.strftime(date_format, models.BodyFatPercentage.date)
        query = (
            db.query(
                date_group.label('date'),
                func.avg(models.BodyFatPercentage.fat_percentage).label('value')
            )
            .filter(
                and_(
                    models.BodyFatPercentage.user_id == user_id,
                    models.BodyFatPercentage.date >= start_date,
                    models.BodyFatPercentage.date <= end_date
                )
            )
            .group_by(date_group)
            .order_by('date')
        )
    
    elif metric_type == "water":
        date_group = func.strftime(date_format, models.WaterConsumption.date)
        query = (
            db.query(
                date_group.label('date'),
                func.avg(models.WaterConsumption.water_amount).label('value')  # Cambiado a promedio
            )
            .filter(
                and_(
                    models.WaterConsumption.user_id == user_id,
                    models.WaterConsumption.date >= start_date,
                    models.WaterConsumption.date <= end_date
                )
            )
            .group_by(date_group)
            .order_by('date')
        )
    
    elif metric_type == "steps":
        date_group = func.strftime(date_format, models.DailyStep.date)
        query = (
            db.query(
                date_group.label('date'),
                func.avg(models.DailyStep.steps_amount).label('value')  # Cambiado a promedio
            )
            .filter(
                and_(
                    models.DailyStep.user_id == user_id,
                    models.DailyStep.date >= start_date,
                    models.DailyStep.date <= end_date
                )
            )
            .group_by(date_group)
            .order_by('date')
        )
    
    elif metric_type == "exercise":
        date_group = func.strftime(date_format, models.Exercise.date)
        query = (
            db.query(
                date_group.label('date'),
                models.Exercise.exercise_name,
                func.count(models.Exercise.exercise_name).label('count'),
                func.sum(models.Exercise.duration).label('duration')
            )
            .filter(
                and_(
                    models.Exercise.user_id == user_id,
                    models.Exercise.date >= start_date,
                    models.Exercise.date <= end_date
                )
            )
            .group_by(date_group, models.Exercise.exercise_name)
            .order_by('date')
        )
        

        results = query.all()
        

        exercise_data = {}
        for result in results:
            date_str = str(result.date)
            if date_str not in exercise_data:
                exercise_data[date_str] = {
                    'exercises': [],
                    'total_duration': 0
                }
            
            exercise_data[date_str]['exercises'].append({
                'name': result.exercise_name,
                'count': result.count,
                'duration': result.duration
            })
            exercise_data[date_str]['total_duration'] += result.duration

        return {
            "dates": list(exercise_data.keys()),
            "data": exercise_data
        }
    

    results = query.all()

    print(
    f"Query results: {results}"
    )
    
    return {
        "dates": [str(result.date) for result in results],
        "values": [float(result.value) for result in results]
    }
