
from pydantic import BaseModel
from typing import Optional

class State(BaseModel):
    name: str

class Data(BaseModel):
    p_name: str
    address: str
    city: str
    state: str

class DataDB(BaseModel):
    p_name: str
    address: str
    city: str
    state_id: Optional[str] = None  # Reference to the state document

class DataResponse(BaseModel):
    id: str
    p_name: str
    address: str
    city: str
    state_id: str

class DataDetailedResponse(BaseModel):
    id: str
    p_name: str
    address: str
    city: str
    state: str


class PropertyNameResponse(BaseModel):
    p_name: str