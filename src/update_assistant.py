# from crm_service import CrmService
from constants import CONFIG_FILE

# from crm_api_service import CrmAPIService


from openai_assitant import OpenAiAssistantService

# from redis_service import RedisService

# from utilities import convert_to_documents, filter_profiles_fields


class MainService:
    def __init__(self):
        self.openai_assistant_service = OpenAiAssistantService(CONFIG_FILE, "OPENAI")


if __name__ == "__main__":
    main_service = MainService()
    main_service.openai_assistant_service.update_assistant_v2()
