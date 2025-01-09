import configparser
import os
import redis

from constants import REDIS_INDEX_NAME
from enums import AccountNumType


class RedisService:
    def __init__(self, config_file, config_name):
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(self.current_folder, config_file)
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.redis_url = config[config_name]["REDIS_URL"]
        self.redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

    def delete_vector(self, account_num_type):
        index_name = self._select_index_name(account_num_type)
        self.redis_client.delete(index_name)

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
