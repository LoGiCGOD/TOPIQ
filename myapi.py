from typing import List
from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from models import *
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from db import fetch_properties_by_city, find_cities_by_state, get_properties_by_city, get_property_by_id, update_property_details
import db

app = FastAPI()


@app.post("/data", response_model=DataResponse)
async def create_data(data: Data):
    state_id = await db.upsert_state(data.state)
    
    data_dict = data.dict()
    data_dict["state_id"] = str(state_id)
    del data_dict["state"]
    
    created_data = await db.insert_data(data_dict)
    
    if created_data:
        return DataResponse(
            id=str(created_data["_id"]),
            p_name=created_data["p_name"],
            address=created_data["address"],
            city=created_data["city"],
            state_id=str(created_data["state_id"])
        )
    else:
        raise HTTPException(status_code=500, detail="Data insertion failed")

@app.get("/fetch_property_details/{city}", response_model=List[str])
async def fetch_property_details(city: str):
    properties = await fetch_properties_by_city(city)
    
    if not properties:
        raise HTTPException(status_code=404, detail="No properties found for this city")
    
    return properties


@app.put("/update_property_details/{property_id}")
async def update_property_details_api(property_id: str, data: Data):
    existing_property = await get_property_by_id(property_id)
    if not existing_property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    updated_details = data.dict(exclude_unset=True)
    await update_property_details(property_id, updated_details)
    updated_property = await get_property_by_id(property_id)
    return updated_property


@app.get("/find_cities_by_state", response_model=List[str])
async def find_cities(
    state_id: Optional[str] = Query(None, alias="state_id"), 
    state_name: Optional[str] = Query(None, alias="state_name")
):
    if not state_id and not state_name:
        raise HTTPException(status_code=400, detail="Either state_id or state_name must be provided")

    if state_id:
        cities = await find_cities_by_state(state_id=state_id)
        if cities:
            return cities

    if state_name:
        cities = await find_cities_by_state(state_name=state_name)
        if cities:
            return cities

    raise HTTPException(status_code=404, detail="State not found or has no cities")



@app.get("/properties/{property_id}", response_model=List[PropertyNameResponse])
async def get_property_names_in_same_city(property_id: str):
    # Fetch the property by ID
    property = await get_property_by_id(property_id)
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Fetch properties in the same city
    city = property["city"]
    properties = await get_properties_by_city(city)
    
    # Extract property names and return them
    return [PropertyNameResponse(p_name=p["p_name"]) for p in properties]