from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=4, max_length=200)


class UserInfo(BaseModel):
    id: int
    name: str
    email: str
    role: Literal["admin", "analyst"]
    active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str
    password: str = Field(min_length=6, max_length=200)
    role: Literal["admin", "analyst"] = "analyst"


class CompanyAssignmentRequest(BaseModel):
    company_ids: List[int]


class CompanyAccessItem(BaseModel):
    id: int
    name: str
    cnpj: Optional[str] = None
    assigned: bool = False
