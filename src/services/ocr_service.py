import configparser
import os

from common.constants import OCR_FOLDER, PDF_FOLDER
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


class OCRService:
    def __init__(self, config_file, config_name):
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(self.current_folder, config_file)
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.WRITE_TO_FILE = config[config_name]["WRITE_TO_FILE"]
        self.DELETE_FILE = config[config_name]["DELETE_FILE"]
        # TODO: comment when deploy to production
        # if os.name == "nt":  # Windows
        #     pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Extract Images from PDF
    def extract_images_from_pdf(self, pdf_file_path, output_folder, dpi=300):
        # Ensure the output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Check if the provided path is a valid file
        if not os.path.isfile(pdf_file_path):
            print(f"The file {pdf_file_path} does not exist.")
            return

        # Ensure the file is a PDF
        if not pdf_file_path.endswith(".pdf"):
            print(f"The file {pdf_file_path} is not a PDF file.")
            return

        # Get the base file name (without extension)
        file_name = os.path.splitext(os.path.basename(pdf_file_path))[0]

        try:
            # TODO: comment when deploy to production
            # Convert PDF pages to images
            # poppler_PATH = os.path.join(self.current_folder, "poppler", "bin")
            # pages = convert_from_path(pdf_file_path, dpi=dpi, poppler_path=poppler_PATH)
            pages = convert_from_path(pdf_file_path, dpi=dpi)
            for page_number, page in enumerate(pages, start=1):
                # Save each page as an image
                image_filename = os.path.join(
                    output_folder, f"{file_name}_page_{page_number}.png"
                )
                page.save(image_filename, "PNG")
                print(f"Saved: {image_filename}")
        except Exception as e:
            print(f"An error occurred: {e}")

        print(f"Images extracted and saved to {output_folder}.")

    def read_text_from_images(self, ocr_path, filename_without_extension):
        text_data = {}

        for image_file in os.listdir(ocr_path):
            if image_file.startswith(
                filename_without_extension
            ) and image_file.endswith((".png", ".jpg", ".jpeg")):
                image_path = os.path.join(ocr_path, image_file)
                text = pytesseract.image_to_string(Image.open(image_path))
                text_data[image_file] = text

        return text_data

    def run(self):
        print("start")

        TARGET_FOLDER = "SIF"
        FOLDER_PATH = os.path.join(self.current_folder, TARGET_FOLDER)

        IMAGE_OUTPUT_FOLDER = os.path.join(self.current_folder, TARGET_FOLDER, "images")
        if not os.path.exists(IMAGE_OUTPUT_FOLDER):
            os.makedirs(IMAGE_OUTPUT_FOLDER)

        TEXT_OUTPUT_FOLDER = os.path.join(self.current_folder, TARGET_FOLDER, "text")
        if not os.path.exists(TEXT_OUTPUT_FOLDER):
            os.makedirs(TEXT_OUTPUT_FOLDER)

        for file in os.listdir(FOLDER_PATH):
            file_name = os.path.splitext(os.path.basename(file))[0]
            self.extract_images_from_pdf(
                pdf_path=FOLDER_PATH + "/" + file, output_folder=IMAGE_OUTPUT_FOLDER
            )
            print(file_name)
            text_results = self.read_text_from_images(
                file_name=file_name, image_folder=IMAGE_OUTPUT_FOLDER
            )
            text_need_to_analyze = "\n".join(text_results.values())
            # print(text_need_to_analyze)
            output_file = f"{TEXT_OUTPUT_FOLDER}/{file_name}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text_need_to_analyze)

        # print([model.id for model in models])
        # result = recognize_text_with_openai(text_need_to_analyze)
        print("DONE")

    def get_text_from_file(self, filename_without_extension, pdf_file_path, ocr_path):
        try:
            self.extract_images_from_pdf(
                pdf_file_path=pdf_file_path, output_folder=ocr_path
            )

            text_from_images = self.read_text_from_images(
                ocr_path,
                filename_without_extension,
            )
            text_results = "\n".join(text_from_images.values())

            if self.WRITE_TO_FILE:
                output_file = f"{ocr_path}/{filename_without_extension}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text_results)

            return text_results

        except Exception as e:
            print(f"Error occurred: {e}")
            return None
        finally:
            # todo: comment for testing
            if self.DELETE_FILE:
                if os.path.exists(output_file):
                    os.remove(output_file)
                # if os.path.exists(pdf_file_path):
                #     os.remove(pdf_file_path)
                # delete png file in ocr folder
                for file in os.listdir(ocr_path):
                    if file.startswith(filename_without_extension) and file.endswith(
                        ".png"
                    ):
                        os.remove(os.path.join(ocr_path, file))
            print("DONE")
