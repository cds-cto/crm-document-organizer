import configparser
import json
import os
import time

from openai import OpenAI

from common.constants import TOKEN_LIMIT_CHUNK_SIZE


class OpenAiAssistantService:
    def __init__(self, config_file, config_name):
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(self.current_folder, config_file)
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.openai_api_key = config[config_name]["OPENAI_API_KEY"]
        self.vector_store_id = config[config_name]["VECTOR_STORE_ID"]
        self.assistant_id = config[config_name]["ASSISTANT_ID_V2"]
        self.time_sleep_for_rate_limit = int(config[config_name]["TIME_SLEEP_FOR_RATE_LIMIT"])

        self.client = OpenAI(api_key=self.openai_api_key)
        self.openai_threads = self.client.beta.threads
        self.openai_assistants = self.client.beta.assistants

    def check_document_type(self, content_file):
        run, thread_id = self.ask_assistant(content_file)
        results = self.assistant_response(run, thread_id)
        return results

    def check_document_type_v2(self, content_file):
        results = self.ask_assistant(content_file)
        return results

    def ask_assistant(self, content_file):
        thread_id = self.openai_threads.create().id

        try:
            chunk_size = TOKEN_LIMIT_CHUNK_SIZE
            chunks = []
            for i in range(0, len(content_file), chunk_size):
                chunk = content_file[i:i + chunk_size]
                # If this is the last chunk and it's smaller than 3000 characters
                if i + chunk_size >= len(content_file) and len(chunk) < 3000 and chunks:
                    # Append to the previous chunk instead of creating a new one
                    chunks[-1] = chunks[-1] + chunk
                else:
                    chunks.append(chunk)

            result_json = {}
            thread_id = self.openai_threads.create().id
            for idx, chunk in enumerate(chunks):
                # base on https://platform.openai.com/account/rate-limits Request and other limits	3 RPM => wait 60 seconds
                print(f"Processing chunk {idx}")
                if idx > 0 and idx % 2 == 0:
                    print(f"Waiting {self.time_sleep_for_rate_limit} seconds for rate limit")
                    thread_id = self.openai_threads.create().id
                    time.sleep(self.time_sleep_for_rate_limit)

                if idx == 0:
                    self.openai_threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content=f"Summarize this text and determine its category type:\n {chunk}",
                    )
                else:
                    self.openai_threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content=f"Given the current category information {result_json}, analyze this text and update the information accurately:\n {chunk}",
                    )

                run = self.openai_threads.runs.create_and_poll(
                    thread_id=thread_id,
                    assistant_id=self.assistant_id,
                )

                if run.status == "completed":
                    messages = self.client.beta.threads.messages.list(
                        thread_id=thread_id
                    )
                    response_content = messages.data[0].content

                    result_json = response_content[0].text.value
                else:
                    print(f"Processing failed:chunk {idx}: {run.last_error}")

            return result_json

            # self.openai_threads.messages.create(
            #     thread_id=thread_id,
            #     role="user",
            #     content=f"Analyze this document to determine its category type:\n {content_file}",
            # )
            # # Use runs to wait for the assistant response
            # run = self.openai_threads.runs.create_and_poll(
            #     thread_id=thread_id,
            #     assistant_id=self.assistant_id,
            # )
            # if run.status == "completed":
            #     messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            #     return messages.data[0].content[0].text.value
            # else:
            #     return run.status

        except Exception as e:
            print(f"Error creating message: {e}")
            return None
        finally:
            self.openai_threads.delete(thread_id=thread_id)

        # is_running = True
        # print("waiting for assistant response.....")
        # while is_running:
        #     run_status = self.openai_threads.runs.retrieve(
        #         thread_id=thread_id, run_id=run.id
        #     )
        #     is_running = run_status.status != "completed"
        #     time.sleep(1)
        # print("assistant response completed")
        # return run, thread_id

    def assistant_response(self, run, thread_id):
        # Get the messages list from the thread
        messages = self.openai_threads.messages.list(thread_id=thread_id)
        # Get the last message for the current run
        last_message = [
            message
            for message in messages.data
            if message.run_id == run.id and message.role == "assistant"
        ][-1]
        # If an assistant message is found, print it
        if last_message:
            return last_message.content[0].text.value
        else:
            return None

    #### update assistant ####
    def update_assistant_old(self):
        openai_assistants = self.client.beta.assistants
        assistant_id = self.assistant_id
        vector_store_id = self.vector_store_id

        assistant = openai_assistants.update(
            assistant_id=assistant_id,
            name="Document Distinction Assistant",
            instructions="""
                Analyze the provided document and compare its content with the characteristics of the categories defined in the knowledge file.
                Based on the comparison, determine and return the single most suitable category that best matches the document's keywords and content.
                Ensure the result strictly adheres to the exact category name as provided in the knowledge file.
                Format the output as:
                {
                    "Category": {<value> where <value> must precisely match a category name from the knowledge file.},
                    "PersonalInformation": {
                    "FirstName": "{First Name or null if not found}",
                    "LastName": "{Last Name or null if not found}",
                    "Last4Ssn": "{Last 4 SSN or null if not found}",
                    "AccountNumber": "{Extract only the numeric digits from the account number if it follows the format xxxxxxx1234. For example, if the account number is xxxxxxx1234, the result should be 1234 or null if not found}",
                    "Address1": "{Address or null if not found}",
                    "State": "{State or null if not found}",
                    "City": "{City or null if not found}",
                    "ZipCode": "{Extract only the main 5-digit ZIP code from the given address, ignoring the extended 4 digits (ZIP+4) or null if not found}"
                    }
                }
                Only return the JSON response in the format above without any explanations or additional text.
             """,
            model="gpt-4o",
            temperature=0,
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
        )
        print(assistant)

    # region  assistant v2
    def update_assistant_v2(self):
        assistant = self.client.beta.assistants.update(
            assistant_id=self.assistant_id,
            name="Document Assistant V2",
            instructions="""
    You are a document analysis expert. I will provide you with various types of documents, and you are strictly required to identify the document category based only on the predefined categories below. You are not allowed to assign any category that is outside the provided list.

Categories and their characteristics are as follows:

Category Descriptions:
- Category: WPOA
  - Document Identification: Source is Citizen Debt Services; requires a wet signature from the client.
  - Keywords: Authorization for banking institution, Authorization to communicate and negotiate.

- Category: POA
  - Document Identification: Source is Citizen Debt Services; requires an e-signature from the client.
  - Keywords: Authorization for banking institution, Authorization to communicate and negotiate.

- Category: NPOA
  - Document Identification: Source is Citizen Debt Services; requires a wet signature from the client and notarization with wet signature from the State and County office, including date and expiration date.
  - Keywords: Authorization for banking institution, Authorization to communicate and negotiate, A notary public, Subscribed and sworn to.

- Category: Bank Statements
  - Document Identification: Source is Creditor.
    - Includes: Summary of amount for the month, Transaction details, Detailed plan.
  - Keywords: Summary of account, New Balance, Previous balance, Statement.

- Category: Collection Notice
  - Document Identification: Source is Debt Collector.
    - Includes: Owner/original creditor information, Original creditor account number, Reference account number, Debt Collector information, Total amount of debt.
  - Keywords: Debt collector, Reference, Debt collection attempt, Our records indicate.

- Category: Legal Notice
  - Document Identification: Source is Court or Lawfirm.
    - Includes: To prepare a lawsuit, To advise that they have authorized to file a lawsuit, Any legal notice that is not summon, judgment, garnishment.
  - Keywords: To prepare a lawsuit, To advise that they have authorized to file a lawsuit.

- Category: Summon Notice
  - Document Identification: Source is Court or Lawfirm.
    - Includes: Have case number, To summon our client, Client required to be attended on online court.
  - Keywords: Summon, You have been sued, You are summoned.

- Category: Default Judgment
  - Document Identification: Source is Court or Lawfirm.
    - Includes: Have case number, To enter a judgment.
  - Keywords: Entry of default, Court judgment, Judgment to be entered.

- Category: Garnishment Notice
  - Document Identification: Source is Court or Lawfirm.
    - Includes: Have case number, To enter garnishment.
  - Keywords: Judgment summary, Garnishee defendant, Garnishment.

- Category: SIF
  - Document Identification: Source is Creditor or Debt Collector
    - Includes: Have a full payment plan and payment date, Have account number, Have current balance, Includes a reduced settlement amount to resolve the debt fully (typically stated as "less than the full balance") , Details on conditions for completing the settlement (e.g., deadlines, voiding terms if payments are missed), Indicates that a confirmation letter will be sent after the final payment is received.
  - Keywords: Settlement agreement, Agree to settle, Less than full balance, Settlement terms, Settlement plan, Final payment confirmation.

- Category: STIP
  - Document Identification: Source is Law firm or County Court.
    - Includes: Have case number, Same as SIF but a law firm form with a signature.
  - Keywords: Stipulation, Payment agreement.

- Category: Payment Confirmation
  - Document Identification: Source is Creditor.
    - Includes: Has payment date, Has payment amount.
  - Keywords: Authorized, Confirmed, Thank you for, payment, Payment received, Payment date, Payment amount.

- Category: Settlement Offer
  - Document Identification: Source is Creditor.
    - Includes: Have balance, Have account number, Have a payment plan with many options, Have phone number to contact to take the offer.
  - Keywords: To help you to pay off your balance, How this offer works.

- Category: Satisfaction Letter
  - Document Identification: Source is Creditor or Debt Collector.
    - Includes: To confirm that the debt has been paid off, Have account number or ending account number, Have reference number.
  - Keywords: Account has been settled, You completed your settlement agreement, The account has been reduced to zero.

Format the output as:
                {
                    "Category": {<value> where <value> must precisely match a category name above},
                    "PersonalInformation": {
                    "FirstName": "{First Name or null if not found}",
                    "LastName": "{Last Name or null if not found}",
                    "Last4Ssn": "{Last 4 SSN or null if not found}",
                    "AccountNumber": "Extract only the numeric digits from the account number, which may be abbreviated as 'Account No' or written as 'Account Number' in documents. Retrieve as many digits as possible, or return null if no numeric digits are found.",
                    "Address1": "{Address or null if not found}",
                    "State": "{State or null if not found}",
                    "City": "{City or null if not found}",
                    "ZipCode": "{Extract only the main 5-digit ZIP code from the given address, ignoring the extended 4 digits (ZIP+4) or null if not found}"
                    }
                }

Strict Instructions:
1. Analyze the provided document content and match it with the categories and keywords described.
2. Ensure that the output contains the exact category name from the list and does not deviate.
3. If the document does not match any category, respond with "null" for the "Category" field.
4. Populate the "PersonalInformation" fields only if such data is explicitly found in the document; otherwise, return "null" for those fields.
You must strictly adhere to the provided categories and formatting in your response.
""",
            model="gpt-4o",
            temperature=0.1,
        )
        print(assistant)

    # endregion assistant v2

    # region vector store
    #### get list of files in a specific vector store ####

    def list_files_in_vector_store(self):
        files = self.client.beta.vector_stores.files.list(
            vector_store_id=self.vector_store_id, limit=100
        )
        return files

    def get_store_info(self):
        store = self.client.beta.vector_stores.retrieve(
            vector_store_id=self.vector_store_id
        )
        return store

    def change_store_inro(self, name):
        store = self.client.beta.vector_stores.update(
            vector_store_id=self.vector_store_id,
            name=name,
        )
        return store

    #### delete all files in a specific vector store ####
    def delete_files_in_vector_store(self):
        files = self.list_files_in_vector_store()

        for file in files.data:
            self.client.beta.vector_stores.files.delete(
                vector_store_id=self.vector_store_id, file_id=file.id
            )
        print("Deleted all files in vector store")

    #### add a file to a specific vector store ####
    def add_file_to_vector_store(self, file_path):
        file_path = os.path.join(self.current_folder, file_path)
        with open(file_path, "rb") as file:
            self.client.beta.vector_stores.files.upload(
                vector_store_id=self.vector_store_id, file=file
            )
        print("Uploaded file to vector store")

    def create_embeddings_and_upload(self, json_file_path, output_file_path):
        """
        Tạo vector store từ file JSON.
        :param json_file_path: Đường dẫn tới file JSON chứa thông tin knowledge.
        """
        # Đọc nội dung từ file JSON
        with open(json_file_path, "r") as f:
            knowledge_data = json.load(f)

        # Chuẩn bị dữ liệu vector
        vectors = []
        for entry in knowledge_data:
            category = entry["Category"]
            keywords = entry["Keywords"]
            metadata = {
                "category": category,
                "document_identification": entry.get("Document Identification", {}),
            }

            # Tạo embedding từ OpenAI API
            for keyword in keywords:
                embedding_response = self.client.embeddings.create(
                    model="text-embedding-ada-002", input=keyword
                )
                embedding = embedding_response.data[0].embedding
                vectors.append(
                    {
                        "id": f"{category}-{keyword}",
                        "embedding": embedding,
                        "metadata": metadata,
                    }
                )

        # Ghi vectors vào tệp .jsonl
        with open(output_file_path, "w") as file:
            json.dump(vectors, file)

        # Tải lên file .jsonl lên Vector Store
        with open(output_file_path, "rb") as file:

            file_upload_response = self.client.beta.vector_stores.files.upload(
                vector_store_id=self.vector_store_id, file=file
            )

        print(f"Tệp đã được tải lên với ID: {file_upload_response}")
        return file_upload_response

    def test_new_vector_store(self):
        vector_store = self.client.beta.vector_stores.create(
            name="DocumentCategorizationVectorStore",
        )

        print(f"Vector Store created with ID: {vector_store}")
        return vector_store

    # endregion vector store
