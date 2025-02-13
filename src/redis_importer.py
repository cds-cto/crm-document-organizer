import json
import os
from common.constants import CONFIG_FILE
import fitz  #


from common.enums import AccountNumType
from services.crm_service import CrmService

from services.langchain_service_v2 import LangChainServiceV2
from services.redis_service import RedisService


class RedisImporter:
    def __init__(self):
        print("init")
        self.langchain_service_v2 = LangChainServiceV2(CONFIG_FILE, "REDIS")
        self.crm_service = CrmService(CONFIG_FILE, "SQL_NEW")
        self.redis_service = RedisService(CONFIG_FILE, "REDIS")

    def delete_all_data(self):
        self.redis_service.delete_all_data()

    def save_data_to_redis_from_documents(self):
        # get all documents from crm
        documents_last4, documents_last12, documents_last16 = (
            self.crm_service.get_profiles_for_vector_store()
        )
        # save to redis
        self.langchain_service_v2.save_documents(documents_last4, AccountNumType.LAST4)
        self.langchain_service_v2.save_documents(
            documents_last12, AccountNumType.LAST12
        )
        self.langchain_service_v2.save_documents(
            documents_last16, AccountNumType.LAST16
        )


if __name__ == "__main__":
    redis_importer = RedisImporter()
    print("check connection success")
    redis_importer.delete_all_data()
    redis_importer.save_data_to_redis_from_documents()
    # main_service.check_POA()
