from pydantic import BaseModel, EmailStr

class UserSignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    company_id: int

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
