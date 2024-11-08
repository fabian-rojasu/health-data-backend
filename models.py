from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    birthday = Column(DateTime, nullable=False)
    gender = Column(String, nullable=False)
    
    weights = relationship("Weight", back_populates="user")
    heights = relationship("Height", back_populates="user")
    body_compositions = relationship("BodyComposition", back_populates="user")
    body_fat_percentages = relationship("BodyFatPercentage", back_populates="user")
    daily_steps = relationship("DailyStep", back_populates="user")
    exercises = relationship("Exercise", back_populates="user")
    water_consumptions = relationship("WaterConsumption", back_populates="user")


class Weight(Base):
    __tablename__ = 'weights'
    
    date = Column(DateTime, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    weight = Column(Float, nullable=False)
    
    user = relationship("User", back_populates="weights")


class Height(Base):
    __tablename__ = 'heights'
    
    date = Column(DateTime, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    height = Column(Float, nullable=False)
    
    user = relationship("User", back_populates="heights")


class BodyComposition(Base):
    __tablename__ = 'body_compositions'
    
    date = Column(DateTime, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    fat = Column(Float, nullable=False)
    muscle = Column(Float, nullable=False)
    water = Column(Float, nullable=False)
    
    user = relationship("User", back_populates="body_compositions")


class BodyFatPercentage(Base):
    __tablename__ = 'body_fat_percentages'
    
    date = Column(DateTime, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    fat_percentage = Column(Float, nullable=False)
    
    user = relationship("User", back_populates="body_fat_percentages")


class DailyStep(Base):
    __tablename__ = 'daily_steps'
    
    date = Column(DateTime, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    steps_amount = Column(Integer, nullable=False)
    
    user = relationship("User", back_populates="daily_steps")


class Exercise(Base):
    __tablename__ = 'exercises'
    
    date = Column(DateTime, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    exercise_name = Column(String, nullable=False)
    duration = Column(Float, nullable=False)  
    
    user = relationship("User", back_populates="exercises")


class WaterConsumption(Base):
    __tablename__ = 'water_consumptions'
    
    date = Column(DateTime, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    water_amount = Column(Float, nullable=False) 
    
    user = relationship("User", back_populates="water_consumptions")