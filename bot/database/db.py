from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import MONGO_URI
import certifi

client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where()
)
db = client["test"]
users_collection = db["users"]
messages_collection = db["messages"]
ratings_collection = db["ratings"]