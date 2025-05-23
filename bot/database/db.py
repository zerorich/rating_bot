from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client["test"]
users_collection = db["users"]
messages_collection = db["messages"]
ratings_collection = db["ratings"]  # Новая коллекция для оценок