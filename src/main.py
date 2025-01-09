# from crm_service import CrmService
import json
import os
from constants import CONFIG_FILE, OCR_FOLDER, PDF_FOLDER

# from crm_api_service import CrmAPIService
from crm_service import CrmService

from enums import AccountNumType
from langchain_service import LangChainService

from langchain_service_v2 import LangChainServiceV2
from ocr_service import OCRService
from openai_assitant import OpenAiAssistantService


from redis_service import RedisService
from utilities import UtilitiesService

# from utilities import convert_to_documents, filter_profiles_fields


class MainService:
    def __init__(self):
        self.langchain_service = LangChainService(CONFIG_FILE, "REDIS")
        self.langchain_service_v2 = LangChainServiceV2(CONFIG_FILE, "REDIS")
        self.ocr_service = OCRService(CONFIG_FILE, "SYSTEM_CONFIG")
        self.openai_assistant_service = OpenAiAssistantService(CONFIG_FILE, "OPENAI")
        self.crm_service = CrmService(CONFIG_FILE, "SQL_NEW")
        self.redis_service = RedisService(CONFIG_FILE, "REDIS")
        self.utilities_service = UtilitiesService()

    def langchain_service_run(self):
        try:
            ## save data to redis from documents
            # self.save_data_to_redis_from_documents()

            ## save data to redis from texts
            self.save_data_to_redis_from_texts()
        except Exception as e:
            print(f"Error langchain service: {str(e)}")
        finally:
            self.crm_service.close()

    def check_document_type_quick(self):
        current_folder = os.path.dirname(os.path.abspath(__file__))
        pdf_files_path = os.path.join(current_folder, "pdf_files", "WPOA")

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
                account_num_type = self.utilities_service.get_account_num_type(
                    profile_info["AccountNumber"]
                )
                query, sub_query = self.utilities_service.render_query_for_search(
                    profile_info, account_num_type
                )

                base_percentage, document_id = (
                    self.langchain_service_v2.query_vector_with_scores_v2(
                        query, sub_query, account_num_type
                    )
                )
                LiabilityId, ProfileId = self.redis_service.get_vector_by_id(
                    document_id.get("id")
                )
                print(LiabilityId, ProfileId)

    def crm_service_run(self):
        try:
            profiles = self.crm_service.get_profiles_for_vector_store()
            print(profiles)
        except Exception as e:
            print(f"Error crm service: {str(e)}")
        finally:
            self.crm_service.close()

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

    def save_data_to_redis_from_texts(self):
        # get all documents from crm
        texts_last4, texts_last12, texts_last16, metadata = (
            self.crm_service.get_profiles_for_text_search()
        )
        # save to redis
        # self.langchain_service_v2.save_from_texts_Cosine_Similarity(texts, metadata)
        self.langchain_service_v2.save_vector(
            texts_last4, metadata, AccountNumType.LAST4
        )
        self.langchain_service_v2.save_vector(
            texts_last12, metadata, AccountNumType.LAST12
        )
        self.langchain_service_v2.save_vector(
            texts_last16, metadata, AccountNumType.LAST16
        )

    def openai_assistant_service_run(self):

        # add file to vector store
        # openai_assistant.add_file_to_vector_store(
        #     file_path="knowledge/knowledge_category.txt"
        # )

        # openai_assistant.update_assistant()

        # store_info = openai_assistant.get_store_info()
        # print(store_info)

        # openai_assistant.change_store_inro(name="Documents Type")
        thread_info = self.openai_assistant_service.get_store_info()
        print(thread_info)

    def ocr_service_run(self, filename):
        # get text from file
        pass

    def check_document(self):
        # try:
        # for testing
        results_data = []
        CATEGORYS = [
            "Bank Statement",
            "Collection Notice",
            "Default Judgment",
            "Garnishment",
            "Legal Notice",
            "NPOA",
            "Payment Confirmation",
            "POA",
            "Satisfaction Letter",
            "Settlement Offer",
            "SIF",
            "STIP",
            "Summon Notice",
            "WPOA",
        ]
        CATEGORY_ORIGINAL = CATEGORYS[12]
        # CATEGORY_ORIGINAL = "test"
        current_folder = os.path.dirname(os.path.abspath(__file__))
        pdf_files_path = os.path.join(current_folder, PDF_FOLDER, CATEGORY_ORIGINAL)
        ocr_path = os.path.join(current_folder, OCR_FOLDER)

        for filename in os.listdir(pdf_files_path):
            if filename.endswith(".pdf"):
                pdf_file_path = os.path.join(pdf_files_path, filename)
                filename_without_extension = os.path.splitext(
                    os.path.basename(filename)
                )[0]
                text_from_file = self.ocr_service.get_text_from_file(
                    filename_without_extension, pdf_file_path, ocr_path
                )
                # check document type
                gpt_response = self.openai_assistant_service.check_document_type_v2(
                    text_from_file
                )
                print(gpt_response)
                # check if gpt_response is None
                if gpt_response == None:
                    results_data.append(
                        {
                            "category_original": CATEGORY_ORIGINAL,
                            "file_name": filename,
                            "gpt_category": None,
                            "gpt_response": None,
                            "db_response": None,
                            "langchain_response": None,
                            "require_human_check": None,
                        }
                    )
                    continue
                # if gpt_response is not None, continue
                gpt_response = (
                    gpt_response.replace("```json", "")
                    .replace("```", "")
                    .replace("\n", "")
                )
                ## convert gpt_response to json
                gpt_response_json = json.loads(gpt_response)

                gpt_category = gpt_response_json["Category"]
                profile_info = gpt_response_json["PersonalInformation"]

                profiles = self.crm_service.find_profiles_from_db(profile_info)

                # region call langchain service to search
                if (
                    profile_info["AccountNumber"] != "null"
                    and profile_info["AccountNumber"] != None
                ):
                    account_num_type = self.utilities_service.get_account_num_type(
                        profile_info["AccountNumber"]
                    )

                    query, sub_query = self.utilities_service.render_query_for_search(
                        profile_info, account_num_type
                    )

                    base_percentage, document_id = (
                        self.langchain_service_v2.query_vector_with_scores_v2(
                            query, sub_query, account_num_type
                        )
                    )
                    if document_id != None:
                        user_data = self.redis_service.get_vector_by_id(
                            document_id.get("id")
                        )
                    else:
                        user_data = None
                        base_percentage = None
                else:
                    user_data = None
                    base_percentage = None
                # endregion

                # region check WPOA and POA
                if gpt_category in ("POA", "WPOA"):
                    gpt_category = (
                        "POA"
                        if self.utilities_service.is_POA(pdf_file_path)
                        else "WPOA"
                    )
                # endregion

                results_data.append(
                    {
                        "category_original": CATEGORY_ORIGINAL,
                        "file_name": filename,
                        "gpt_category": gpt_category,
                        "gpt_response": json.dumps(profile_info),
                        "db_response": json.dumps(profiles),
                        "langchain_response": json.dumps(user_data),
                        "percentage": base_percentage,
                        "require_human_check": base_percentage == None
                        or base_percentage < 80,
                    }
                )

        self.utilities_service.create_excel_file(
            f"{CATEGORY_ORIGINAL}.xlsx", results_data
        )

    # except Exception as e:
    #     print(f"Error checking documents: {str(e)}")
    #     print(f"Error file: {e.__traceback__.tb_frame.f_code.co_filename}")
    #     print(f"Error line: {e.__traceback__.tb_lineno}")

    # finally:
    #     # self.crm_service.close()
    #     pass


if __name__ == "__main__":
    main_service = MainService()
    # main_service.crm_service_run()
    # main_service.document_type_update()

    main_service.check_document()
    # main_service.openai_assistant_service_run()
    # main_service.langchain_service_run()
    # main_service.openai_assistant_service.update_assistant()
    # main_service.save_data_to_redis_from_texts()
    # main_service.save_data_to_redis_from_documents()

    # main_service.check_document_type_quick()

    # store_info = main_service.openai_assistant_service.get_store_info()
    # print(store_info)
