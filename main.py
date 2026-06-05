from fastapi import FastAPI, Depends
from db import user, device, device_statuse, get_db
from datetime import datetime
from pydantic import BaseModel
import statistics
from typing import Optional
from sqlalchemy.orm import Session


class UserCreate(BaseModel):
    name: str
    email: str


class DeviceAdd(BaseModel):
    name: str
    user_id: int


class GetStat(BaseModel):
    x: float
    y: float
    z: float


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "Worldввввв!"}


@app.get("/users")
def show_users(db: Session = Depends(get_db)):
    all_users = db.query(user).all()
    return [{"id": p.id, "name": p.name, "email": p.email} for p in all_users]


@app.get("/users/{user_id}")
def user_info(user_id: int, db: Session = Depends(get_db)):
    some_user = db.query(user).filter(user.id == user_id).first()
    if some_user is None:
        return "No such user!"
    else:
        return [{"id": some_user.id, "name": some_user.name, "email": some_user.email}]


@app.get("/users/{user_id}/devices")
def user_devices_info(user_id: int, db: Session = Depends(get_db)):
    some_user = db.query(user).filter(user.id == user_id).first()
    if some_user is None:
        return "No such user!"
    else:
        user_devices = db.query(device).filter(device.user_id == user_id).all()
        names = [d.name + '\n' for d in user_devices]
        if len(names) == 0:
            names = "No devices yet."
    return {"user": some_user.name, "devices": [{"id": d.id, "name": d.name} for d in user_devices]}


@app.get("/users/{user_id}/devices/{device_id}/statistics/analysis")
def show_analysis(user_id: int, device_id: int, from_date: Optional[datetime] = None,
                  to_date: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(device_statuse).filter(device_statuse.device_id == device_id)
    if from_date:
        query = query.filter(device_statuse.time >= from_date)
    if to_date:
        query = query.filter(device_statuse.time <= to_date)
    stats = query.all()
    if not stats:
        return {"error": "No data for this device"}
    x_values = [s.x for s in stats]
    y_values = [s.y for s in stats]
    z_values = [s.z for s in stats]
    return {
        "device_id": device_id,
        "x": {"min": min(x_values), "max": max(x_values), "count": len(x_values), "sum": sum(x_values),
              "median": statistics.median(x_values)},
        "y": {"min": min(y_values), "max": max(y_values), "count": len(y_values), "sum": sum(y_values),
              "median": statistics.median(y_values)},
        "z": {"min": min(z_values), "max": max(z_values), "count": len(z_values), "sum": sum(z_values),
              "median": statistics.median(z_values)}}


@app.get("/users/{user_id}/statistics/analysis")
def show_all_analysis(user_id: int, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None,
                      db: Session = Depends(get_db)):
    user_devices = db.query(device).filter(device.user_id == user_id).all()
    num_of_dev = len(user_devices)
    results = []
    for dev in user_devices:
        query = db.query(device_statuse).filter(device_statuse.device_id == dev.id)
        if from_date:
            query = query.filter(device_statuse.time >= from_date)
        if to_date:
            query = query.filter(device_statuse.time <= to_date)
        stats = query.all()
        results.append({
            "device_id": dev.id,
            "x": [s.x for s in stats],
            "y": [s.y for s in stats],
            "z": [s.z for s in stats],
        })
    if not results:
        return {"error": "No data for this user devices"}
    x_values = [x for r in results for x in r["x"]]
    y_values = [y for r in results for y in r["y"]]
    z_values = [z for r in results for z in r["z"]]
    if not x_values:
        return {"error": "No stats for this user's devices"}
    return {
        "user_id": user_id,
        "number_of_devices": num_of_dev,
        "x": {"min": min(x_values), "max": max(x_values), "count": len(x_values), "sum": sum(x_values),
              "median": statistics.median(x_values)},
        "y": {"min": min(y_values), "max": max(y_values), "count": len(y_values), "sum": sum(y_values),
              "median": statistics.median(y_values)},
        "z": {"min": min(z_values), "max": max(z_values), "count": len(z_values), "sum": sum(z_values),
              "median": statistics.median(z_values)}}


@app.post("/register")
def reg_user(data: UserCreate, db: Session = Depends(get_db)):
    some_user = user(name=data.name, email=data.email)
    db.add(some_user)
    db.commit()
    return {
        "id": some_user.id,
        "message": "User created"
    }


@app.post("/device")
def add_device(data: DeviceAdd, db: Session = Depends(get_db)):
    some_user = db.query(user).filter(user.id == data.user_id).first()
    if not some_user:
        return {"error": "User not found"}
    some_device = device(name=data.name, user_id=data.user_id)
    db.add(some_device)
    db.commit()
    return {
        "id": some_user.id,
        "message": "Device added"
    }


@app.post("/devices/{device_id}/statistics")
def get_stat(device_id: int, data: GetStat, db: Session = Depends(get_db)):
    some_time = datetime.now()
    some_stat = device_statuse(device_id=device_id, x=data.x, y=data.y, z=data.z, time=some_time)
    db.add(some_stat)
    db.commit()
