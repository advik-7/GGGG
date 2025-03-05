# operations.py
import os
import asyncio
from collections import Counter
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

# Load environment variables
load_dotenv()

# Get MongoDB Credentials
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Encode credentials
encoded_username = quote_plus(MONGO_USERNAME)
encoded_password = quote_plus(MONGO_PASSWORD)

# Construct MongoDB URI
MONGO_URI = f"mongodb+srv://{encoded_username}:{encoded_password}@{MONGO_HOST}/?retryWrites=true&w=majority"

# Pydantic Models
class WarehouseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    warehouse_id: str = Field(..., alias="_id")
    product_1: Optional[str] = None
    product_2: Optional[str] = None
    product_3: Optional[str] = None
    product_4: Optional[str] = None
    product_5: Optional[str] = None
    product_6: Optional[str] = None
    product_7: Optional[str] = None
    product_8: Optional[str] = None
    product_9: Optional[str] = None
    product_10: Optional[str] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)

class TransportingModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    route: str = Field(..., alias="_id")
    product_1: Optional[str] = None
    product_2: Optional[str] = None
    product_3: Optional[str] = None
    product_4: Optional[str] = None
    product_5: Optional[str] = None
    product_6: Optional[str] = None
    product_7: Optional[str] = None
    product_8: Optional[str] = None
    product_9: Optional[str] = None
    product_10: Optional[str] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)

# MongoDB Connection
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

# Collections
warehouses_collection = db["Warehouses"]
transporting_collection = db["Transporting"]
unique_codes_collection = db["UniqueCodes"]

async def get_product_id_by_code(code_id: str) -> Optional[str]:
    """
    Retrieve the product ID associated with a given unique code from MongoDB.
    """
    try:
        code_entry = await unique_codes_collection.find_one({"code_id": code_id})
        if code_entry:
            return code_entry.get("product_id")
        else:
            print(f"No product found for code: {code_id}")
            return None
    except Exception as e:
        print(f"Error retrieving product ID for code {code_id}: {e}")
        return None

async def add_transporting(route: str, count: str, Client_id: str):
    try:
        # Prepare the document with product information
        transport_data = {"_id": route}
        product_field = Client_id
        transport_data[product_field] = f":{count}"
        result = await transporting_collection.insert_one(transport_data)
        return result.inserted_id
    except Exception as e:
        print(f"Error adding transporting record: {e}")
        return None

def clean_value(value):
    """Remove ':' prefix and convert to integer safely."""
    if value is None:
        return 0
    return int(value.lstrip(":")) if isinstance(value, str) and value.startswith(":") else int(value)

def subtract_transport_values(dict1, list2):
    result = {}
    # Convert list of tuples to a dictionary, cleaning values
    dict2 = {key: clean_value(value) for key, value in list2}
    for key in dict1.keys():
        val1 = clean_value(dict1[key])
        val2 = dict2.get(key, 0)
        result[key] = val1 - val2
    return result

async def delete_transporting(route: str):
    try:
        # Check if the document exists
        existing_document = await transporting_collection.find_one({"_id": route})
        if not existing_document:
            print("No record found for the given route.")
            return None
        # Extract all values before deleting
        extracted_values = {key: value for key, value in existing_document.items() if key != "_id"}
        # Delete the entire document
        delete_result = await transporting_collection.delete_one({"_id": route})
        return extracted_values if delete_result.deleted_count > 0 else None
    except Exception as e:
        print(f"Error deleting transporting record: {e}")
        return None

async def update_warehouse(warehouse_id: str, count: str, Client_id: str):
    update_messages = []
    warehouse = await warehouses_collection.find_one({"_id": warehouse_id})
    print("Warehouse ID:", warehouse_id)
    product_field = Client_id
    # Prepare update operations
    update_operations = {}
    update_operations[Client_id] = f"{count}"
    update_messages.append(f"Added {product_field} to {product_field}")
    existing_count = warehouse[product_field]
    if product_field == Client_id:
        new_count = int(existing_count) - int(count)
        update_operations[Client_id] = f"{new_count}"
        update_messages.append(f"Updated {product_field} count to {new_count}")
    else:
        print("new")
    if update_operations:
        await warehouses_collection.update_one({"_id": warehouse_id}, {"$set": update_operations})
    return update_messages

async def Receive_warehouse(warehouse_id: str, count: str, Client_id: str):
    update_messages = []
    warehouse = await warehouses_collection.find_one({"_id": warehouse_id})
    product_field = Client_id
    update_operations = {}
    update_operations[Client_id] = f"{count}"
    update_messages.append(f"Added {product_field} to {product_field}")
    existing_count = warehouse[product_field]
    if product_field == Client_id:
        new_count = int(existing_count) + int(count)
        update_operations[Client_id] = f"{new_count}"
        update_messages.append(f"Updated {product_field} count to {new_count}")
    else:
        print("new")
    if update_operations:
        await warehouses_collection.update_one({"_id": warehouse_id}, {"$set": update_operations})
    return update_messages

async def run_multiple_scans(n):
    """
    Perform multiple QR code scans and return product counts.
    Returns:
        List of tuples with (product_name, count)
    """
    from qr_scanner import scan_qr  # Import here to avoid circular import issues
    results = []
    for _ in range(n):
        try:
            # Run the synchronous scan_qr() in a thread
            code = await asyncio.to_thread(scan_qr)
            print(f"Scanned QR Code: {code}")
            product_id = await get_product_id_by_code(code)
            if product_id:
                print(f"Product ID for code {code}: {product_id}")
                results.append(product_id)
            else:
                print(f"Code {code} not found in the database")
        except Exception as e:
            print(f"Scan error: {e}")
    product_counts = Counter(results)
    return [(product, count) for product, count in product_counts.items()]

async def send_operation(warehouse_id: str, address: str, n: int):
    """
    Handles the send operation.
    """
    transporting_id = f"{warehouse_id}-{address}"
    inventory = await run_multiple_scans(n)
    result_messages = []
    for product_name, count in inventory:
        transporting_result = await add_transporting(transporting_id, count, product_name)
        if transporting_result:
            result_messages.append(f"Inserted Transporting ID: {transporting_result}")
            update_messages = await update_warehouse(warehouse_id, count, product_name)
            result_messages.extend(update_messages)
        else:
            result_messages.append("Failed to add transporting record")
    return result_messages

async def receive_operation(warehouse_id: str, address: str, n: int):
    """
    Handles the receive operation.
    """
    transporting_id = f"{warehouse_id}-{address}"
    transport_record = await delete_transporting(transporting_id)
    inventory = await run_multiple_scans(n)
    res = subtract_transport_values(transport_record, inventory)
    status = "No material lost" if all(value == 0 for value in res.values()) else "Material lost"
    result_messages = [status]
    for product_name, count in inventory:
        update_messages = await Receive_warehouse(warehouse_id, count, product_name)
        result_messages.extend(update_messages)
    return result_messages
