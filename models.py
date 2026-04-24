from fastapi import HTTPException
from database import Base
from sqlalchemy import(
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
    Column,
    event,
    JSON
)
from sqlalchemy.ext.mutable import MutableList
from typing_extensions import List,Dict,Any
from sqlalchemy.orm import Mapped,relationship,mapped_column
import uuid
from datetime import datetime,timezone

import qrcode
import os
from pathlib import Path

QR_DIR = Path(os.path.join(os.getcwd(),"media/qr"))
QR_DIR.mkdir(parents=True, exist_ok=True)



def generate_qr(consignment_id: str):
    qr = qrcode.make(consignment_id)

    file_path = QR_DIR / f"{consignment_id}{str(datetime.utcnow())}.png"
    qr.save(file_path)

    return str(file_path)

user_consignment = Table(
    "user_consignments",
    Base.metadata,
    Column("user_id", ForeignKey("Users.user_id"), primary_key=True),
    Column("consignment_id", ForeignKey("Consignments.consignment_id"), primary_key=True)
)

class User(Base):
    __tablename__ = "Users"

    user_id:Mapped[str]  = mapped_column(String,unique=True,nullable=False,primary_key=True,default=lambda: str(uuid.uuid4()))
    username:Mapped[str] = mapped_column(String(50),unique=True,nullable=False)
    password:Mapped[str] = mapped_column(String,nullable=False)
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,default=lambda: datetime.now(timezone.utc))
    email:Mapped[str] = mapped_column(String(100),nullable=True,unique=True)
    profile:Mapped["Profile"] = relationship(back_populates="user")
    consignments:Mapped[List["Consignment"]] = relationship(
        secondary=user_consignment,
        back_populates="users"
    )
    logs:Mapped[List["Log"]] = relationship(back_populates="user")

class Profile(Base):
    __tablename__ = "Profiles"

    id:Mapped[int] = mapped_column(Integer,index=True,unique=True,nullable=False,primary_key=True)
    firstname:Mapped[str] = mapped_column(String,nullable=True,unique=False)
    lastname:Mapped[str] = mapped_column(String,nullable=True,unique=False)
    address:Mapped[str] = mapped_column(String,nullable=True)
    role:Mapped[str] = mapped_column(String,nullable=False,unique=False)
    work_location:Mapped[str] = mapped_column(String,nullable=False)
    user:Mapped["User"] = relationship(back_populates='profile')
    user_id:Mapped[str] = mapped_column(ForeignKey("Users.user_id"),nullable=False,unique=True)

class Consignment(Base):
    __tablename__ = "Consignments"

    consignment_id:Mapped[str] = mapped_column(String,unique=True,index=True,nullable=False,primary_key=True,default=lambda: str(uuid.uuid4()))
    qr_code:Mapped[str] = mapped_column(String,nullable=False,unique=True)
    image:Mapped[str] = mapped_column(String,nullable=False,unique=True)
    consignment_name:Mapped[str] = mapped_column(String(200),nullable=True,unique=False)
    source:Mapped[str] = mapped_column(String,nullable=True,unique=False)
    destination:Mapped[str] = mapped_column(String,nullable=True,unique=False)
    destination_pincode:Mapped[str] = mapped_column(String,nullable=False,unique=False)
    employee_ids:Mapped[str] = mapped_column(JSON,nullable=True,unique=False,default=list)
    paths:Mapped["DeliveryRoute"] = relationship(back_populates="consignment")
    track_logs:Mapped[List["tracking_log"]] = relationship(back_populates="consignment")
    users:Mapped[List["User"]] = relationship(
        secondary=user_consignment,
        back_populates="consignments",
    )



class Log(Base):
    __tablename__ = "Logs"

    id:Mapped[int] = mapped_column(Integer,unique=True,primary_key=True,index=True,nullable=False)
    status:Mapped[str] = mapped_column(String,unique=False,nullable=False,default="Logged in")
    user_agent:Mapped[str] = mapped_column(String,unique=False,nullable=False)
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))
    user:Mapped["User"] = relationship(back_populates="logs")
    user_id:Mapped[str] = mapped_column(ForeignKey("Users.user_id"),nullable=False)

class tracking_log(Base):
    __tablename__ = "Tracking Logs"

    id:Mapped[int] = mapped_column(Integer,unique=True,primary_key=True,index=True,nullable=False)
    current_location:Mapped[str] = mapped_column(String,nullable=False)
    current_coordinates:Mapped[str] = mapped_column(String,nullable=True)
    arrival_time:Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),nullable=False)
    status:Mapped[str] = mapped_column(String,nullable=True)
    consignment:Mapped["Consignment"] = relationship(back_populates="track_logs")
    consignment_id:Mapped[str] = mapped_column(ForeignKey("Consignments.consignment_id"))
    
    @property
    def current_log(self):
        if self.status == "Dispatched":
            log = f"{self.status} from {self.current_location} at {self.arrival_time}."
        if self.status == "Arrived":
            log = f"{self.status} at {self.current_location} at {self.arrival_time}."
        if self.status == "Delivered":
            log = f"{self.status} at {self.current_location} on {self.arrival_time}."
        return log

class DeliveryRoute(Base):
    __tablename__ = "Paths"

    id:Mapped[int] = mapped_column(Integer,unique=True,primary_key=True,index=True,nullable=False)
    hub:Mapped[str] = mapped_column(String,nullable=False,index=True)
    delivery_stops:Mapped[List[str]] = mapped_column(JSON,nullable=True,default=list)
    nearest_hubs:Mapped[List[str]] = mapped_column(JSON,nullable=False,default=list)
    nearest_warehouse:Mapped[List[str]] = mapped_column(JSON,nullable=False,default=list)
    consignment:Mapped["Consignment"] = relationship(back_populates="paths")
    consignment_id:Mapped[ str] = mapped_column(ForeignKey("Consignments.consignment_id"))

class Routing(Base):
    __tablename__ = "Routing"

    id:Mapped[int] = mapped_column(Integer,unique=True,primary_key=True,index=True,nullable=False)
    hub:Mapped[str] = mapped_column(String,nullable=False,index=True,unique=True)
    route:Mapped[List[str]] = mapped_column(JSON,nullable=False,default=list)

@event.listens_for(tracking_log,"before_insert")
def filter_status(mapper,connection,target):
    Status = ["Dispatched","Delivered","Arrived"]
    if target.status in Status:
        target.status = target.status
    else:
        raise HTTPException(status_code=400,detail="Invalid Status for delivery.")


@event.listens_for(Profile,"before_insert")
def filter_role(mapper,connection,target):
    Roles = ["Manufacturer","Deliveryman","Warehouse employee"]
    if target.role in Roles:
        target.role = target.role
    else:
        raise HTTPException(status_code=400,detail="Invalid Role.")

