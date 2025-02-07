import configparser
import os
import boto3
from common.constants import OCR_FOLDER, PDF_FOLDER
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


class S3Service:
    def __init__(self, config_file, config_name):
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(self.current_folder, config_file)
        config = configparser.ConfigParser()
        config.read(config_file_path)

        # config load
        self.aws_access_key_id = config[config_name]["AWS_ACCESS_KEY_ID"]
        self.aws_secret_access_key = config[config_name]["AWS_SECRET_ACCESS_KEY"]
        self.region_name = config[config_name]["REGION"]
        self.bucket_name = config[config_name]["BUCKET_NAME"]
        self.folder_name = config[config_name]["FOLDER_NAME"]
        self.s3_client = boto3.client("s3", **self._load_config())

    def _load_config(self):
        """Load AWS credentials"""
        return {
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "region_name": self.region_name,
        }
    def download_file_by_name_s3(self, list_file_name):
        try:
            # Create pdf_files directory if it doesn't exist
            pdf_dir = os.path.join(os.path.dirname(self.current_folder), PDF_FOLDER)
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)

            for file_name in list_file_name:
                try:
                    local_file_path = os.path.join(pdf_dir, os.path.basename(file_name))
                    self.s3_client.download_file(
                        self.bucket_name,
                        self.folder_name + "/" + file_name,
                        local_file_path,
                    )
                except Exception as e:
                    print(f"Error downloading file: {file_name}")
                    return False
            return True

        except Exception as e:
            print(f"Error searching/downloading files: {file_name}")
            return False
