
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