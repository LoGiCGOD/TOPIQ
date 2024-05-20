from typing import List
from fastapi import FastAPI, HTTPException, Query
from models import *
from db import fetch_properties_by_city, find_cities_by_state, get_properties,  get_state_id, update_property_with_state,  upsert_and_insert_data

app = FastAPI()


@app.post("/data", response_model=DataDetailedResponse)
async def create_data(data: Data):
    data_dict = data.dict()
    created_data = await upsert_and_insert_data(data_dict)
    if created_data:
        created_data["id"] = str(created_data.pop("_id"))
        return created_data
    else:
        raise HTTPException(status_code=500, detail="Data insertion failed")
    
    
@app.get("/fetch_property_details/{city}", response_model=List[str])
async def fetch_property_details(city: str):
    properties = await fetch_properties_by_city(city)
    if not properties:
        raise HTTPException(status_code=404, detail="No properties found for this city")
    return properties

@app.put("/update_property_details/{property_id}", response_model=DataDetailedResponse)
async def update_property_details_api(property_id: str, data: Data):
    data_dict = data.dict(exclude_unset=True)
    
    state_id = await get_state_id(data_dict["state"])
    # Update the property details with state ID
    data_dict["state_id"] = str(state_id["_id"])
    data_dict["state"] = state_id["name"]
    updated_property = await update_property_with_state(property_id, data_dict)
    
    if not updated_property:
        raise HTTPException(status_code=404, detail="Property not found")
    return DataDetailedResponse(**updated_property)


@app.get("/find_cities_by_state", response_model=List[str])
async def find_cities(
    state_id: Optional[str] = Query(None, alias="state_id"), 
    state_name: Optional[str] = Query(None, alias="state_name")
):
    if not state_id and not state_name:
        raise HTTPException(status_code=400, detail="Either state_id or state_name or both must be provided")
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
    properties = await get_properties(property_id)
    return properties
    
    
    





    