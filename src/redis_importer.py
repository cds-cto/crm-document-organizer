# from crm_service import CrmService
import json
import os
from common.constants import CONFIG_FILE
import fitz  #

# from crm_api_service import CrmAPIService


from common.enums import AccountNumType
from services.crm_service import CrmService
from services.langchain_service import LangChainService

# from openai_assitant import OpenAiAssistantService
from services.langchain_service_v2 import LangChainServiceV2
from services.openai_assitant import OpenAiAssistantService
from common.utilities import UtilitiesService


# from utilities import convert_to_documents, filter_profiles_fields


class MainService:
    def __init__(self):
        print("init")
        self.langchain_service_v2 = LangChainServiceV2(CONFIG_FILE, "REDIS")
        # self.ocr_service = OCRService(CONFIG_FILE, "SYSTEM_CONFIG")
        # self.openai_assistant_service = OpenAiAssistantService(CONFIG_FILE, "OPENAI")
        # self.crm_api_service = CrmAPIService(CONFIG_FILE, "CRM")
        self.crm_service = CrmService(CONFIG_FILE, "SQL_NEW")
        # self.redis_service = RedisService(CONFIG_FILE, "REDIS")
        # self.openai_chat_service = OpenAiService(CONFIG_FILE, "OPENAI")
        # self.utilities_service = UtilitiesService()
        pass

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
    main_service = MainService()
    print("check connection success")
    main_service.save_data_to_redis_from_documents()
    # main_service.check_POA()
