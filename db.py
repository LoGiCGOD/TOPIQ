from typing import Dict, List
from fastapi import HTTPException
from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


# MongoDB client setup
MONGO_URI = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
database = client["my_database"]  
data_collection = database["data"]  
state_collection = database["state"]  


async def upsert_and_insert_data(data_dict: Dict):

        state_doc = await state_collection.find_one_and_update(
            {"name": data_dict["state"]},
            {"$setOnInsert": {"name": data_dict["state"]}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        data_dict["state_id"] = state_doc["_id"]

        # Find existing data or insert new data
        updated_data = await data_collection.find_one_and_update(
            {"p_name": data_dict["p_name"]},
            {"$setOnInsert": data_dict},  
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        # If a new document was inserted, include the state name
        if updated_data is not None and "state" not in updated_data:
            updated_data["state"] = state_doc["name"]
        return updated_data


async def fetch_properties_by_city(city: str) -> List[str]:
    properties = await data_collection.find({"city": city}).distinct("p_name")
    return properties

async def get_state_id(state_name: str):
    state_doc = await state_collection.find_one({"name": state_name})
    if state_doc:
        return state_doc
    else:
        result = await state_collection.insert_one({"name": state_name})
        state_doc = await state_collection.find_one({"_id": result.inserted_id})
        return state_doc
    
async def update_property_with_state(property_id: str, data_dict: Dict):
    state_id = ObjectId(data_dict["state_id"])
    # Update the property details
    updated_data = await data_collection.find_one_and_update(
        {"_id": ObjectId(property_id)},
        {"$set": {
            "p_name": data_dict["p_name"],
            "address": data_dict["address"],
            "city": data_dict["city"],
            "state": data_dict["state"],
            "state_id": state_id
        }},
        return_document=ReturnDocument.AFTER
    )

    if updated_data is not None:
        updated_data["id"] = str(updated_data.pop("_id"))
        return updated_data
    else:
        return None


async def find_cities_by_state(state_id: str = None, state_name: str = None) -> List[str]:
    query = {}
    if state_id:
        try:
            query["state_id"] = ObjectId(state_id)
        except:
            return []
    elif state_name:
        state_doc = await state_collection.find_one({"name": state_name})
        if state_doc:
            query["state_id"] = state_doc["_id"]
        else:
            return []
    cities = await data_collection.distinct("city", query)
    return cities

async def get_properties(property_id: str) -> List[dict]:
    try:
        # Fetch property details
        property_doc = await data_collection.find_one({"_id": ObjectId(property_id)})
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        city = property_doc.get("city")
        cursor = data_collection.find({"city": city}, {"_id": 0, "p_name": 1})  # retrieve only p_name
        properties = await cursor.to_list(length=None)
        print(properties)
        if not properties:
            raise HTTPException(status_code=404, detail="No properties found")
        return properties

    except Exception as e:
        print(f"Error getting properties: {e}")
        return []



