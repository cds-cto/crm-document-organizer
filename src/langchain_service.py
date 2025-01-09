# from langchain.vectorstores import Redis
# from langchain.embeddings import HuggingFaceEmbeddings
import configparser
import json
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.redis import Redis
from datetime import datetime

from constants import NUMBER_OF_DOCUMENTS_TO_RETURN, REDIS_INDEX_NAME


class LangChainService:
    def __init__(self, config_file, config_name):
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(self.current_folder, config_file)
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.redis_url = config[config_name]["REDIS_URL"]
        self.index_name = REDIS_INDEX_NAME

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
        self.vector_store = Redis(
            redis_url=self.redis_url,
            embedding=self.embedding,
            index_name=self.index_name,
            vector_schema=vector_schema,  # Sử dụng FLAT schema
        )

    def save_vector(self, documents):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] start save vector from documents...")

        from concurrent.futures import ThreadPoolExecutor

        # chunk size
        chunk_size = 100
        document_chunks = [
            documents[i : i + chunk_size] for i in range(0, len(documents), chunk_size)
        ]
        self.saved_count = 0
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.map(self._save_vector, document_chunks)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Vector stored successfully!")

    def save_from_texts(self, texts, metadata):

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] start save vector from texts...")

        Redis.from_texts(
            texts,
            self.embedding,
            metadatas=metadata,
            redis_url=self.redis_url,
            index_name=self.index_name,
        )
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Vector stored successfully!")

    def save_from_texts_Cosine_Similarity(self, texts, metadata):

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] start save vector from texts...")

        Redis.from_texts(
            texts,
            self.embedding,
            metadatas=metadata,
            redis_url=self.redis_url,
            index_name="users_cosine_similarity_olc",
            distance_metric="COSINE",
        )
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Vector stored successfully!")

    def _save_vector(self, document_chunk):

        self.vector_store.add_documents(
            documents=document_chunk,
        )
        self.saved_count += 1
        # save vector successfully
        print(f"Vector chunk {self.saved_count} stored successfully!")

    def query_vector(self, query):
        # simple
        results = self.vector_store.similarity_search(query)
        meta = results[1].metadata
        print("Key of the document in Redis: ", meta.pop("id"))
        print("Metadata of the document: ", meta)
        return results

    def query_vector_with_scores(self, query):
        # simple
        results = self.vector_store.similarity_search_with_score(
            query, k=NUMBER_OF_DOCUMENTS_TO_RETURN
        )
        for doc, score in results:
            print(f"Content: {doc.page_content}")
            print(f"Metadata: {doc.metadata}")
            print(f"Score: {score}")
            print()

        return results

    def advanced_search(self, query):
        pass
        # update the results  base on weight point
        results = self.vector_store.similarity_search_with_score(json.dumps(query))

        # Process results
        for i, (doc, score) in enumerate(results):
            print(f"Document {i+1}:")
            print(f"Similarity Score: {score}")

            # Accessing metadata
            metadata = doc.metadata

            # Extract specific parameters from metadata
            author = metadata.get(
                "FirstName", "Unknown"
            )  # Default to "Unknown" if not found
            date = metadata.get("LastName", "Unknown")
            topic = metadata.get("City", "Unknown")

            # Print extracted metadata
            print(f"Author: {author}")
            print(f"Date: {date}")
            print(f"Topic: {topic}")
            print("-" * 50)

        results_with_scores = [
            (result[0], self.calculate_priority_score(result, query))
            for result in results
        ]
        return results_with_scores
