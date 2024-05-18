from typing import List
from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


# MongoDB client setup
MONGO_URI = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
database = client["my_database"]  # Database name
data_collection = database["data"]  # Collection name for property data
state_collection = database["state"]  # Collection name for states


async def upsert_state(state_name):
    state_doc = await state_collection.find_one_and_update(
        {"name": state_name},
        {"$setOnInsert": {"name": state_name}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return state_doc["_id"]

async def insert_data(data_dict):
    new_data = await data_collection.insert_one(data_dict)
    return await data_collection.find_one({"_id": new_data.inserted_id})


async def fetch_properties_by_city(city: str) -> List[str]:
    properties = await data_collection.find({"city": city}).distinct("p_name")
    return properties


async def get_property_by_id(property_id: str):
    property_id_obj = ObjectId(property_id)
    property_doc = await data_collection.find_one({"_id": property_id_obj})
    if property_doc:
        property_doc.pop("state_id", None)  # Exclude state_id field
        property_doc["_id"] = str(property_doc["_id"])  # Convert ObjectId to string
    return property_doc

async def update_property_details(property_id: str, updated_details: dict):
    property_id_obj = ObjectId(property_id)
    await data_collection.update_one({"_id": property_id_obj}, {"$set": updated_details})


async def find_cities_by_state(state_id: str = None, state_name: str = None) -> List[str]:
    query = {}
    if state_id:
        query["state_id"] = state_id
    elif state_name:
        state_doc = await state_collection.find_one({"name": state_name})
        if state_doc:
            query["state_id"] = str(state_doc["_id"])
        else:
            return []

    cities = await data_collection.distinct("city", query)
    return cities


async def get_properties_by_city(city: str) -> List[dict]:
    try:
        properties = await data_collection.find({"city": city}).to_list(length=100)
        return properties
    except Exception as e:
        print(f"Error getting properties by city: {e}")
        return []