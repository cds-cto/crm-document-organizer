import os
import pandas as pd
import fitz
import openpyxl
from openpyxl.styles import Alignment
from common.enums import AccountNumType


class UtilitiesService:
    def get_account_num_type(self, account_num):
        if len(account_num) <= 4:
            return AccountNumType.LAST4
        elif len(account_num) <= 12:
            return AccountNumType.LAST12
        elif len(account_num) <= 16:
            return AccountNumType.LAST16
        else:
            return None

    def render_query_for_search(self, profile_info, account_num_type):
        query = f"{profile_info['FirstName']} {profile_info['LastName']} lives at {profile_info['Address1']}, {profile_info['City']}, {profile_info['State']} {profile_info['ZipCode']}. "
        sub_query = ""
        if profile_info["Last4Ssn"] != "null":
            query += f"Last4Ssn: {profile_info['Last4Ssn']}. "
        if profile_info["AccountNumber"] != "null" and account_num_type != None:
            account_num = profile_info["AccountNumber"]
            if account_num_type == AccountNumType.LAST4:
                query += f"Last4CurrentAccountNumbers: {account_num} or Last4AccountNumbers: {account_num}."
                sub_query = f"Last4CurrentAccountNumbers: {account_num} or Last4AccountNumbers: {account_num}."
            elif account_num_type == AccountNumType.LAST12:
                query += f"Last12CurrentAccountNumbers: {account_num} or Last12AccountNumbers: {account_num}."
                sub_query = f"Last12CurrentAccountNumbers: {account_num} or Last12AccountNumbers: {account_num}."
            elif account_num_type == AccountNumType.LAST16:
                query += f"Last16CurrentAccountNumbers: {account_num} or Last16AccountNumbers: {account_num}."
                sub_query = f"Last16CurrentAccountNumbers: {account_num} or Last16AccountNumbers: {account_num}."
        return query, sub_query

    # create excel file
    def create_excel_file(self, filename, data):

        df = pd.DataFrame(data)

        # Create Excel writer with openpyxl engine
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

            # Access worksheet to adjust dimensions
            worksheet = writer.sheets["Sheet1"]

            # Set row height for all rows (excluding header)
            for idx in range(
                2, len(df) + 2
            ):  # 2 because Excel is 1-based and header takes row 1
                worksheet.row_dimensions[idx].height = 70

            # Set column width for all columns
            for col in worksheet.columns:
                if col[0].column_letter in ["D", "E", "F"]:
                    worksheet.column_dimensions[col[0].column_letter].width = 70
                    # Enable text wrapping and top alignment for columns D, E, F
                    for cell in col:
                        cell.alignment = Alignment(wrap_text=True, vertical="top")
                else:
                    worksheet.column_dimensions[col[0].column_letter].width = 20

    # check if the file is POA
    def is_POA(self, file_path):
        if file_path.endswith(".pdf"):
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
        else:
            raise Exception("File is not a PDF")
