# from langchain.vectorstores import Redis

import configparser
import json
import os

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.redis import Redis
from datetime import datetime
from constants import NUMBER_OF_DOCUMENTS_TO_RETURN, REDIS_INDEX_NAME
from enums import AccountNumType
from concurrent.futures import ThreadPoolExecutor
from langchain_community.vectorstores.redis import RedisTag
from langchain_community.vectorstores import FAISS
from langchain.schema import Document


class LangChainServiceV2:
    def __init__(self, config_file, config_name):
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(self.current_folder, config_file)
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.redis_url = config[config_name]["REDIS_URL"]
        self.index_name = "users_flat_cosine"

        model_name = "sentence-transformers/all-mpnet-base-v2"
        encode_kwargs = {"normalize_embeddings": True}
        self.embedding = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs=encode_kwargs,
        )
        vector_schema = {
            "algorithm": "FLAT",  # Sử dụng FLAT để tìm kiếm chính xác
            "distance_metric": "COSINE",  # Sử dụng Cosine Similarity
        }
        self.vector_store_last4 = Redis(
            redis_url=self.redis_url,
            embedding=self.embedding,
            index_name="users_flat_last4",
            vector_schema=vector_schema,  # Sử dụng FLAT schema
        )
        self.vector_store_last12 = Redis(
            redis_url=self.redis_url,
            embedding=self.embedding,
            index_name="users_flat_last12",
            # vector_schema=vector_schema,  # Sử dụng FLAT schema
        )
        self.vector_store_last16 = Redis(
            redis_url=self.redis_url,
            embedding=self.embedding,
            index_name="users_flat_last16",
            # vector_schema=vector_schema,  # Sử dụng FLAT schema
        )

    def _select_vector_store(self, account_num_type):
        if account_num_type == AccountNumType.LAST4:
            return self.vector_store_last4
        elif account_num_type == AccountNumType.LAST12:
            return self.vector_store_last12
        elif account_num_type == AccountNumType.LAST16:
            return self.vector_store_last16

    def save_documents(self, documents, account_num_type):

        print("start save vector from documents...")

        vector_store = self._select_vector_store(account_num_type)
        # chunk size
        chunk_size = 100
        documents_chunks = [
            documents[i : i + chunk_size] for i in range(0, len(documents), chunk_size)
        ]

        self.saved_count = 0
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = [
                executor.submit(self._save_documents, documents_chunks[i], vector_store)
                for i in range(len(documents_chunks))
            ]
            for future in futures:
                future.result()

        print(f"Total chunks saved successfully: {self.saved_count}")

    def _save_documents(self, documents, vector_store):
        vector_store.add_documents(documents)
        self.saved_count += 1
        # save vector successfully

        print(f"Vector chunk {self.saved_count} stored successfully!")

    def save_vector(self, texts, metadatas, account_num_type):
        print("start save vector from documents...")

        vector_store = self._select_vector_store(account_num_type)
        # chunk size
        chunk_size = 100
        texts_chunks = [
            texts[i : i + chunk_size] for i in range(0, len(texts), chunk_size)
        ]
        metadata_chunks = [
            metadatas[i : i + chunk_size] for i in range(0, len(metadatas), chunk_size)
        ]

        self.saved_count = 0
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    self._save_vector, texts_chunks[i], metadata_chunks[i], vector_store
                )
                for i in range(len(texts_chunks))
            ]
            for future in futures:
                future.result()

        print(f"Total chunks saved successfully: {self.saved_count}")

    def _save_vector(self, texts, metadatas, vector_store):
        vector_store.add_texts(
            texts,
            metadatas=metadatas,
        )
        self.saved_count += 1
        # save vector successfully
        print(f"Vector chunk {self.saved_count} stored successfully!")

    def query_vector(self, query):
        # simple
        results = self.vector_store.similarity_search(
            query, k=NUMBER_OF_DOCUMENTS_TO_RETURN
        )
        meta = results[1].metadata
        print("Key of the document in Redis: ", meta.pop("id"))
        print("Metadata of the document: ", meta)
        return results

    def query_vector_with_scores(self, query, sub_query, account_num_type):
        # simple
        try:
            print("query: ", query)
            vector_store = self._select_vector_store(account_num_type)
            results = vector_store.similarity_search_with_score(
                query, k=NUMBER_OF_DOCUMENTS_TO_RETURN
            )

            for doc, score in results:
                print(f"Content: {doc.page_content}")
                print(f"Metadata: {doc.metadata}")
                print(f"Score: {score}")

            return results
        except Exception as e:
            #  if Number of documents to return is != 1 => return -1
            return results, -1

    #### Query vector store with adjusted scoring based on account number matches ####

    def query_vector_with_scores_v2(self, query, sub_query, account_num_type):
        """
        Returns:
            tuple: (match_percentage, document_id) if match found, (None, 0, 0) if no match
                  match_percentage is similarity score converted to percentage
                  document_id is metadata ID of matched document
        """
        try:
            print("query: ", query)
            vector_store = self._select_vector_store(account_num_type)
            results = vector_store.similarity_search_with_score(
                query, k=NUMBER_OF_DOCUMENTS_TO_RETURN
            )

            sorted_results = self.adjusted_result(results, sub_query)
            # return first result
            if sorted_results:
                content, score, base_score, document_id = sorted_results[0]
                # Convert scores to percentages
                base_percentage = (1 - base_score) * 100
                print(
                    f"Content: {content}\nScore: {score}\nBase percentage: {base_percentage:.2f}%\n"
                )
                return base_percentage, document_id

            return None, None

        except Exception as e:
            return None, None

    #### search bổ sung trên tập kết quả: ####
    def query_vector_with_scores_v3(self, query, sub_query, account_num_type):
        # simple
        try:
            print("query: ", query)
            vector_store = self._select_vector_store(account_num_type)
            results = vector_store.similarity_search_with_score(
                query, k=NUMBER_OF_DOCUMENTS_TO_RETURN
            )

            documents = [result[0] for result in results]
            vector_store = FAISS.from_documents(documents, self.embedding)

            # Query bổ sung để tìm kiếm trên kết quả trả ra
            results = vector_store.similarity_search(sub_query, k=1)

            # Hiển thị kết quả sau khi tìm kiếm bổ sung
            for result in results:
                print(f"Content: {result.page_content}\nMetadata: {result.metadata}\n")

        except Exception as e:
            return None, 0, 0

    def adjusted_result(self, results, sub_query):

        # reduce score if sub_query match
        adjusted_results = []
        account_nums = sub_query.split("or")
        current_account_num = account_nums[0].strip()
        account_num = account_nums[1].strip()

        for content, score in results:
            content_text = content.page_content
            id = content.metadata
            base_score = score
            if sub_query != "":
                # reduce score if sub_query match
                if f"{current_account_num}" in content_text:
                    score -= 0.1
                elif f"{account_num}" in content_text:
                    score -= 0.05
            adjusted_results.append((content_text, score, base_score, id))

        # sort by score
        sorted_results = sorted(adjusted_results, key=lambda x: x[1])

        # for content, score, base_score in sorted_results:
        #     print(f"Content: {content}\nScore: {score}\nBase Score: {base_score}\n")

        return sorted_results

    # def advanced_search(self, query):
    # def advanced_search(self, query):
    #     pass
    #     # update the results  base on weight point
    #     results = self.redis_store.similarity_search_with_score(json.dumps(query))

    #     # Process results
    #     for i, (doc, score) in enumerate(results):
    #         print(f"Document {i+1}:")
    #         print(f"Similarity Score: {score}")

    #         # Accessing metadata
    #         metadata = doc.metadata

    #         # Extract specific parameters from metadata
    #         author = metadata.get(
    #             "FirstName", "Unknown"
    #         )  # Default to "Unknown" if not found
    #         date = metadata.get("LastName", "Unknown")
    #         topic = metadata.get("City", "Unknown")

    #         # Print extracted metadata
    #         print(f"Author: {author}")
    #         print(f"Date: {date}")
    #         print(f"Topic: {topic}")
    #         print("-" * 50)

    #     results_with_scores = [
    #         (result[0], self.calculate_priority_score(result, query))
    #         for result in results
    #     ]
    #     return results_with_scores
