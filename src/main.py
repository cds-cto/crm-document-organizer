# project import
from src.routers import crm_document_organizer_router

# third party import
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

# nest_asyncio.apply()

# # Debug
# import debugpy
# debugpy.listen(("0.0.0.0", 5679))


# ********** Initialize FastAPI
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, title="CTSAPI v2")

# ********** Initialize CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Router
app.include_router(crm_document_organizer_router.router)

# Initialize security
security = HTTPBasic()

# Authentication credentials
SWAGGER_USERNAME = "master"
SWAGGER_PASSWORD = "secretsecret2025"


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, SWAGGER_USERNAME)
    is_password_correct = secrets.compare_digest(credentials.password, SWAGGER_PASSWORD)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


# ********** OpenAPI


@app.get("/openapi.json")
async def get_open_api_endpoint(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    return JSONResponse(get_openapi(title="Citizen Debt Services API 2", version="1", routes=app.routes))


# ********** Docs


@app.get("/docs")
async def get_documentation(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="CTSAPI v2.1 Swagger",
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    )


# if __name__ == '__main__':
#     uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)


# # from crm_service import CrmService
# import datetime
# import json
# import os
# import debugpy
# from common.constants import (
#     CATEGORY_DICTIONARY,
#     CONFIG_FILE,
#     OCR_FOLDER,
#     PDF_FOLDER,
#     USERNAME_UPDATE_STATUS,
# )

# # from crm_api_service import CrmAPIService
# from common.enums import AccountNumType, UnMappedDocumentStatus
# from services.crm_service import CrmService
# # from services.langchain_service import LangChainService
# # from services.langchain_service_v2 import LangChainServiceV2
# from services.ocr_service import OCRService
# from services.openai_assitant import OpenAiAssistantService
# from services.redis_service import RedisService
# from common.utilities import UtilitiesService
# from services.s3_service import S3Service

# # from utilities import convert_to_documents, filter_profiles_fields


# class MainService:
#     def __init__(self):
#         # self.langchain_service = LangChainService(CONFIG_FILE, "REDIS")
#         self.crm_service = CrmService(CONFIG_FILE, "SQL_NEW")
#         print("crm_service init success")
#         self.s3_service = S3Service(CONFIG_FILE, "AWS")
#         print("s3_service init success")

#     def save_data_to_redis_from_documents(self):
#         # get all documents from crm
#         documents_last4, documents_last12, documents_last16 = (
#             self.crm_service.get_profiles_for_vector_store()
#         )
#         # save to redis
#         # self.langchain_service_v2.save_documents(documents_last4, AccountNumType.LAST4)
#         # self.langchain_service_v2.save_documents(
#         #     documents_last12, AccountNumType.LAST12
#         # )
#         # self.langchain_service_v2.save_documents(
#         #     documents_last16, AccountNumType.LAST16
#         # )

#     def update_assistant(self):
#         self.openai_assistant_service.update_assistant_v2()

#     ### check file type with single file
#     def check_document_type_with_single_file(self):
#         MY_FILE_NAME = "1P4R4ZDFKC20241120185006.txt"

#         current_folder = os.path.dirname(os.path.abspath(__file__))
#         my_files_path = os.path.join(current_folder, "ocr_files", MY_FILE_NAME)

#         with open(my_files_path, "r", encoding="utf8") as file:
#             text_from_file = file.read()

#             gpt_response = self.openai_assistant_service.check_document_type_v2(
#                 text_from_file
#             )
#             print(gpt_response)

#             # gpt_response = (
#             #     gpt_response.replace("```json", "").replace("```", "").replace("\n", "")
#             # )
#             # ## convert gpt_response to json
#             # gpt_response_json = json.loads(gpt_response)

#             # call langchain service to search

#             # profiles = self.crm_db_service.find_profiles_from_db(profile_info)

#             # simple search
#             # query = self.utilities_service.render_query_for_search(profile_info)

#             # langchain_response, score = (
#             #     self.langchain_service_v2.query_vector_with_scores(query)
#             # )
#             # print(langchain_response, score)

#     def check_document(self):
#         # try:
#         # for testing
#         results_data = []
#         CATEGORYS = [
#             "Bank Statement",  # 0
#             "Collection Notice",  # 1
#             "Default Judgment",  # 2
#             "Garnishment",  # 3
#             "Legal Notice",  # 4
#             "NPOA",  # 5
#             "Payment Confirmation",  # 6
#             "POA",  # 7
#             "Satisfaction Letter",  # 8
#             "Settlement Offer",  # 9
#             "SIF",  # 10
#             "STIP",  # 11
#             "Summon Notice",  # 12
#             "WPOA",  # 13
#             "SIF2",  # 14
#             "STIP2",  # 15
#             "Payment Confirmation2",  # 16
#         ]
#         CATEGORY_ORIGINAL = CATEGORYS[16]
#         # CATEGORY_ORIGINAL = "test"
#         current_folder = os.path.dirname(os.path.abspath(__file__))
#         pdf_files_path = os.path.join(current_folder, PDF_FOLDER, CATEGORY_ORIGINAL)
#         ocr_path = os.path.join(current_folder, OCR_FOLDER)

#         for filename in os.listdir(pdf_files_path):
#             if filename.endswith(".pdf"):
#                 pdf_file_path = os.path.join(pdf_files_path, filename)
#                 filename_without_extension = os.path.splitext(
#                     os.path.basename(filename)
#                 )[0]
#                 text_from_file = self.ocr_service.get_text_from_file(
#                     filename_without_extension, pdf_file_path, ocr_path
#                 )
#                 # check document type
#                 gpt_response = self.openai_assistant_service.check_document_type_v2(
#                     text_from_file
#                 )
#                 print(gpt_response)
#                 # check if gpt_response is None
#                 if gpt_response == None:
#                     results_data.append(
#                         {
#                             "category_original": CATEGORY_ORIGINAL,
#                             "file_name": filename,
#                             "gpt_category": None,
#                             "gpt_response": None,
#                             "db_response": None,
#                             "langchain_response": None,
#                             "require_human_check": None,
#                         }
#                     )
#                     continue
#                 # if gpt_response is not None, continue
#                 gpt_response = (
#                     gpt_response.replace("```json", "")
#                     .replace("```", "")
#                     .replace("\n", "")
#                 )
#                 ## convert gpt_response to json
#                 gpt_response_json = json.loads(gpt_response)

#                 gpt_category = gpt_response_json["Category"]
#                 profile_info = gpt_response_json["PersonalInformation"]

#                 profiles = self.crm_service.find_profiles_from_db(profile_info)

#                 # region call langchain service to search
#                 # TODO: Testing 2/21/25
#                 user_data = None
#                 base_percentage = None
                
#                 # if (
#                 #     profile_info["AccountNumber"] != "null"
#                 #     and profile_info["AccountNumber"] != None
#                 # ):
#                 #     account_num_type = self.utilities_service.get_account_num_type(
#                 #         profile_info["AccountNumber"]
#                 #     )

#                 #     query, sub_query = self.utilities_service.render_query_for_search(
#                 #         profile_info, account_num_type
#                 #     )

#                 #     base_percentage, document_id = (
#                 #         self.langchain_service_v2.query_vector_with_scores_v2(
#                 #             query, sub_query, account_num_type
#                 #         )
#                 #     )
#                 #     if document_id != None:
#                 #         user_data = self.redis_service.get_vector_by_id(
#                 #             document_id.get("id")
#                 #         )
#                 #     else:
#                 #         user_data = None
#                 #         base_percentage = None
#                 # else:
#                 #     user_data = None
#                 #     base_percentage = None
#                 # endregion

#                 # region check WPOA and POA
#                 if gpt_category in ("POA", "WPOA"):
#                     gpt_category = (
#                         "POA"
#                         if self.utilities_service.is_POA(pdf_file_path)
#                         else "WPOA"
#                     )
#                 # endregion

#                 results_data.append(
#                     {
#                         "category_original": CATEGORY_ORIGINAL,
#                         "file_name": filename,
#                         "gpt_category": gpt_category,
#                         "gpt_response": json.dumps(profile_info),
#                         "db_response": json.dumps(profiles),
#                         "langchain_response": json.dumps(user_data),
#                         "percentage": base_percentage,
#                         "require_human_check": base_percentage == None
#                         or base_percentage < 80,
#                     }
#                 )

#         self.utilities_service.create_excel_file(
#             f"{CATEGORY_ORIGINAL}.xlsx", results_data
#         )

#         # except Exception as e:
#         #     print(f"Error checking documents: {str(e)}")
#         #     print(f"Error file: {e.__traceback__.tb_frame.f_code.co_filename}")
#         #     print(f"Error line: {e.__traceback__.tb_lineno}")

#         # finally:
#         #     # self.crm_service.close()
#         #     pass

#     def find_category_profileID_liabilityID(self):
#         try:
#             # for testing
#             unmapped_documents = self.crm_service.get_unmapped_documents()
#             print(len(unmapped_documents))
#             all_file_name = []

#             for unmapped_document in unmapped_documents:
#                 print(unmapped_document)
#                 document_id = str(unmapped_document[0])
#                 file_name = str(unmapped_document[1])
#                 self.s3_service.download_file_by_name_s3([file_name])

#                 current_folder = os.path.dirname(os.path.abspath(__file__))

#                 pdf_files_path = os.path.join(current_folder, PDF_FOLDER)
#                 ocr_path = os.path.join(current_folder, OCR_FOLDER)

#                 if file_name.endswith(".pdf"):
#                     pdf_file_path = os.path.join(pdf_files_path, file_name)
#                     all_file_name.append(pdf_file_path)
#                     filename_without_extension = os.path.splitext(
#                         os.path.basename(file_name)
#                     )[0]
#                     text_from_file = self.ocr_service.get_text_from_file(
#                         filename_without_extension, pdf_file_path, ocr_path
#                     )
#                     # check document type
#                     gpt_response = self.openai_assistant_service.check_document_type_v2(
#                         text_from_file
#                     )
#                     print(gpt_response)
#                     # check if gpt_response is None
#                     if gpt_response == None:
#                         self.crm_service.update_unmapped_documents(
#                             {
#                                 "DocumentId": document_id,
#                                 "Category": None,
#                                 "ProfileId": None,
#                                 "LiabilityId": None,
#                                 "Status": UnMappedDocumentStatus.PENDING.value,
#                                 "UpdatedBy": USERNAME_UPDATE_STATUS,
#                                 "UpdatedAt": datetime.datetime.now().strftime(
#                                     "%Y-%m-%d %H:%M:%S"
#                                 ),
#                             }
#                         )
#                         continue
#                     # if gpt_response is not None, continue
#                     gpt_response = (
#                         gpt_response.replace("```json", "")
#                         .replace("```", "")
#                         .replace("\n", "")
#                     )
#                     ## convert gpt_response to json
#                     gpt_response_json = json.loads(gpt_response)

#                     gpt_category = gpt_response_json["Category"]

#                     # region check WPOA and POA
#                     if gpt_category in ("POA", "WPOA"):
#                         gpt_category = (
#                             "POA"
#                             if self.utilities_service.is_POA(pdf_file_path)
#                             else "WPOA"
#                         )
#                     # endregion

#                     profile_info = gpt_response_json["PersonalInformation"]

#                     profiles = self.crm_service.find_profiles_from_db(profile_info)

#                     # region call langchain service to search
#                     # TODO: Testing 2/21/25
#                     user_data = None
#                     # if (
#                     #     profile_info["AccountNumber"] != "null"
#                     #     and profile_info["AccountNumber"] != None
#                     # ):
#                     #     account_num_type = self.utilities_service.get_account_num_type(
#                     #         profile_info["AccountNumber"]
#                     #     )

#                     #     query, sub_query = (
#                     #         self.utilities_service.render_query_for_search(
#                     #             profile_info, account_num_type
#                     #         )
#                     #     )

#                     #     base_percentage, redis_document_id = (
#                     #         self.langchain_service_v2.query_vector_with_scores_v2(
#                     #             query, sub_query, account_num_type
#                     #         )
#                     #     )

#                     #     if redis_document_id != None:
#                     #         user_data = self.redis_service.get_vector_by_id(
#                     #             redis_document_id.get("id")
#                     #         )
#                     #     else:
#                     #         user_data = None
#                     #         base_percentage = None
#                     # else:
#                     #     user_data = None
#                     #     base_percentage = None
#                     # endregion

#                     # region update unmapped document
#                     profile_id = None
#                     liability_id = None

#                     if profiles:
#                         profile_id = profiles["ProfileId"]
#                         liability_id = profiles["LiabilityId"]
#                     elif user_data:
#                         profile_id = user_data["profile_id"] 
#                         liability_id = user_data["liability_id"]

#                     if profile_id and liability_id:
#                         if not self.crm_service.is_liability_belong_to_profile(
#                             liability_id, profile_id
#                         ):
#                             liability_id = None

#                     self.crm_service.update_unmapped_documents(
#                         {
#                             "DocumentId": document_id,
#                             "Category": None if gpt_category in [None, "null"] else CATEGORY_DICTIONARY[gpt_category],
#                             "ProfileId": profile_id,
#                             "LiabilityId": liability_id,
#                             "Status": UnMappedDocumentStatus.PENDING.value,
#                             "UpdatedBy": USERNAME_UPDATE_STATUS,
#                             "UpdatedAt": datetime.datetime.now().strftime(
#                                 "%Y-%m-%d %H:%M:%S"
#                             ),
#                         }
#                     )
#                 # endregion

#         except Exception as e:
#             print(f"Error checking documents: {str(e)}")
#         finally:
#             self.crm_service.close()
#             # remove all file in unmapped_documents
#             for file_name in all_file_name:
#                 if os.path.exists(file_name):
#                     os.remove(file_name)


# if __name__ == "__main__":
#     # debugpy.listen(("0.0.0.0", 5679))
#     # debugpy.wait_for_client()
#     print("start success")
#     main_service = MainService()

#     main_service.find_category_profileID_liabilityID()
#     # main_service.check_document_type_with_single_file()
#     print("end success")