######################## STRUCTURE CONFIG ########################
PDF_FOLDER = "pdf_files"
OCR_FOLDER = "ocr_files"
CONFIG_FILE = "config.ini"

######################## LANGCHAIN CONFIG ########################

NUMBER_OF_DOCUMENTS_TO_RETURN = 20

######################## REDIS CONFIG ########################

REDIS_INDEX_NAME = "users"

######################## OPENAI CONFIG ########################

TOKEN_LIMIT_CHUNK_SIZE = 20000

######################## CRM CONFIG ########################
CHUNK_SIZE = 100
FUZZY_SEARCH_TOLERANCE = 1

######################## CONSTANTS ID ########################
PRIMARY_ADDRESS_ID = "5ba9cf57-608f-424d-9385-f543a2708baf"
USERNAME_UPDATE_STATUS = "97289D14-2305-4953-9213-14F598F6E4E7"
LIABILITY_ID_DEFAULT = "00000000-0000-0000-0000-000000000000"

######################## CONSTANTS CATEGORY ########################
# create dictionary with key as the category and value as the category id
CATEGORY_DICTIONARY = {
    "Satisfaction Letter": "0887B8E0-4501-410B-948C-18519FFEED05",
    "Payment Confirmation": "12C42774-2121-42C9-859A-1F761FC280EB",
    "Garnishment Notice": "842C729E-5312-4F16-AE8B-3167C75A1512",
    "Settlement Letters": "30983EF7-FF93-445F-820E-52D99FCA76C8",
    "Judgement Notice": "4AF088E5-9D8B-4338-A010-602819040EA5",
    "Summon Notice": "94421A67-708C-4FD6-B618-7AE4FF09A7FB",
    "Legal Notice": "FC8367D2-C896-4A51-901C-8298264D3EAE",
    "POA": "94C17769-9F7E-4674-8DB1-94A2C5C715F4",
    "Collection Notice": "0DC4AAB9-3E67-420F-B3FF-94F4DB97CF8F",
    "Bank Statement": "8733B3AD-2CEA-4ED9-BFE4-A85F9E68B743",
    "Settlement Offer": "561BF4E8-9A03-4882-BCC4-F7A4E7CEF380",
    "NPOA": "7C129CFE-B26B-469F-8F70-F839CB6E60CA",
    "WPOA": "9E1CF4A2-C213-4D70-B762-7BFAE9679738",
    "STIP": "A12634E1-D212-47F4-A3CE-8DF5AA663BDD",
    "SIF": "30983EF7-FF93-445F-820E-52D99FCA76C8",
}


######################## AWS CONFIG ########################
