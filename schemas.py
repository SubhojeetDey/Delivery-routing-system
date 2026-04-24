from pydantic import BaseModel,Field,EmailStr
from typing_extensions import Dict,Any

class User(BaseModel):
    username:str
    password:str
    email:str
    role:str
    work_location:str
    address:str

    class Config:
        from_attributes = True
    
class Token(BaseModel):
    access_token:str
    token_type:str

    class Config:
        from_attributes = True

class CreateConsignment(BaseModel):
    consignment_name:str
    tracker:str
    dispatched_from:str
    destination:str

    class Config:
        from_attributes = True
    
class GetConsignment(BaseModel):
    consignment_name:str
    source:str
    destination:str
    image:str
    destination_pincode:str
    qr_code:str
    consignment_id:str

    class Config:
        from_attributes=True

class Consignment(BaseModel):
    consignment_name:str
    source:str
    destination:str
    destination_pincode:str
    image:str
    qr_code:str
    consignment_id:str

    class Config:
        from_attributes=True

class UpdateConsignment(BaseModel):
    consignment_name:str = Field(default=None) 
    source:str = Field(default=None)
    destination:str = Field(default=None)
    destination_pincode:str = Field(default=None)

    class Config:
        from_attributes=True

class Profile(BaseModel):
    firstname:str = Field(default=None)
    lastname:str = Field(default=None)
    address:str = Field(default=None)

    class Config:
        from_attributes=True

class path(BaseModel):
    nearest_hubs:Dict[str, Any]
    nearest_warehouse:Dict[str, Any]

    class Config:
        from_attributes=True

class Routing(BaseModel):
    hubs:str
    vehicle:int

    class Config:
        from_attributes=True

class GetRouting(BaseModel):
    hub:str
    route:list

    class Config:
        from_attributes=True

class Paths(BaseModel):
    source:str
    destination:str

    class Config:
        from_attributes=True

class GetRoute(BaseModel):
    route:Dict[str, Any]

    class Config:
        from_attributes=True

class WorkLocation(BaseModel):
    work_location:str
    class Config:
        from_attributes=True