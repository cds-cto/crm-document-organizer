import configparser
import os
import redis
from langchain_community.vectorstores.redis import Redis
from common.enums import AccountNumType


class RedisService:
    def __init__(self, config_file, config_name):
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(self.current_folder, config_file)
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.redis_url = config[config_name]["REDIS_URL"]
        # Parse redis URL to get host and port
        redis_parts = self.redis_url.replace("redis://", "").split(":")
        redis_host = redis_parts[0]
        redis_port = int(redis_parts[1]) if len(redis_parts) > 1 else 6379
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

        # Print total number of keys in Redis
        total_keys = len(self.redis_client.keys("*"))
        print(f"Total number of Redis keys: {total_keys}")

    def delete_all_data(self):
        """Delete all keys and data from Redis"""
        self.redis_client.flushall()
        print("All data has been deleted from Redis")

    def get_vector_by_id(self, key_id: str) -> dict:
        retrieved_data = self.redis_client.hgetall(key_id)
        # Handle binary data - decode only the specific fields we need
        try:
            user_data = {
                "liability_id": retrieved_data.get(b"LiabilityId", b"").decode(
                    "utf-8", errors="ignore"
                ),
                "profile_id": retrieved_data.get(b"ProfileId", b"").decode(
                    "utf-8", errors="ignore"
                ),
                "content": retrieved_data.get(b"content", b"").decode(
                    "utf-8", errors="ignore"
                ),
            }
        except UnicodeDecodeError:
            user_data = {
                "liability_id": "",
                "profile_id": "",
                "content": "",
            }

        return user_data
