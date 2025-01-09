# from crm_service import CrmService
import json
import os
from constants import CONFIG_FILE
import fitz  #

# from crm_api_service import CrmAPIService
# from crm_db_service import CrmDBService


from langchain_service import LangChainService

# from openai_assitant import OpenAiAssistantService
from langchain_service_v2 import LangChainServiceV2
from utilities import UtilitiesService


# from utilities import convert_to_documents, filter_profiles_fields


class MainService:
    def __init__(self):
        self.langchain_service_v2 = LangChainServiceV2(CONFIG_FILE, "REDIS")
        # self.ocr_service = OCRService(CONFIG_FILE, "SYSTEM_CONFIG")
        # self.openai_assistant_service = OpenAiAssistantService(CONFIG_FILE, "OPENAI")
        # self.crm_api_service = CrmAPIService(CONFIG_FILE, "CRM")
        # self.crm_db_service = CrmDBService(CONFIG_FILE, "SQL_NEW")
        # self.redis_service = RedisService(CONFIG_FILE, "REDIS")
        # self.openai_chat_service = OpenAiService(CONFIG_FILE, "OPENAI")
        self.utilities_service = UtilitiesService()
        pass

    def check_document_type_quick(self):
        current_folder = os.path.dirname(os.path.abspath(__file__))
        pdf_files_path = os.path.join(current_folder, "pdf_files", "POA")

        for filename in os.listdir(pdf_files_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(pdf_files_path, filename)
                with open(file_path, "r", encoding="utf8") as file:
                    text_from_file = file.read()

                gpt_response = self.openai_assistant_service.check_document_type_v2(
                    text_from_file
                )
                print(gpt_response)

                gpt_response = (
                    gpt_response.replace("```json", "")
                    .replace("```", "")
                    .replace("\n", "")
                )
                ## convert gpt_response to json
                gpt_response_json = json.loads(gpt_response)

                gpt_category = gpt_response_json["Category"]
                profile_info = gpt_response_json["PersonalInformation"]

                # call langchain service to search

                # profiles = self.crm_db_service.find_profiles_from_db(profile_info)

                # simple search
                query = self.utilities_service.render_query_for_search(profile_info)

                langchain_response, score = (
                    self.langchain_service_v2.query_vector_with_scores(query)
                )
                print(langchain_response, score)

    def check_POA(self):
        current_folder = os.path.dirname(os.path.abspath(__file__))
        pdf_files_path = os.path.join(current_folder, "pdf_files", "WPOA")
        for filename in os.listdir(pdf_files_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(pdf_files_path, filename)
                result = "POA" if self.is_POA(file_path) else "NOT POA"
                print(f"{filename}: {result}")

    def is_POA(self, file_path):
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc, start=1):
            images = page.get_images(full=True)
            if page_num == 2:
                ### Page 2 of the POA does not contain any images
                if not images:
                    return True
                ### contains images and the image is too small => POA
                for img in images:
                    image_info = doc.extract_image(img[0])
                    if image_info["width"] < 300 and image_info["height"] < 100:
                        return True
        doc.close()


if __name__ == "__main__":
    main_service = MainService()

    main_service.check_document_type_quick()
    # main_service.check_POA()
