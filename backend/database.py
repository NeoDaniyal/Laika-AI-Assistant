import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "ai_chatbot"


client = AsyncIOMotorClient(MONGODB_URL)
db = client[DB_NAME]
chats_collection = db["chats"]