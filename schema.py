
from fastapi import File, UploadFile
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    birthday: str
    gender: str
    
class LoginRequest(BaseModel):
    email: str
    password: str
    
class ImportDataRequest(BaseModel):
    user_id: int
    file_type: str
    file: UploadFile = File(...)