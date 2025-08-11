import boto3
import botocore.exceptions
from trp import Document
from tabulate import tabulate

def extract_textract_signatures_and_fields(image_path):
    """
    Analyze a local image with Amazon Textract to extract signature blocks and 'Signature' form fields.

    Args:
        image_path (str): Path to the image or PDF file.

    Returns:
        dict: {
            "signatures": list of (Id, Geometry),
            "fields": list of (Key, Value)
        }
    """
    textract = boto3.client('textract')

    # Read the document
    try:
        with open(image_path, 'rb') as document:
            image_bytes = bytearray(document.read())
    except FileNotFoundError:
        print(f"File not found: {image_path}")
        return None

    # Analyze document with FORMS and SIGNATURES
    try:
        response = textract.analyze_document(
            Document={'Bytes': image_bytes},
            FeatureTypes=["FORMS", "SIGNATURES"]
        )
    except botocore.exceptions.BotoCoreError as e:
        print(f"Textract API error: {e}")
        return None

    # Extract SIGNATURE blocks
    signature_blocks = []
    for item in response.get("Blocks", []):
        if item.get("BlockType") == "SIGNATURE":
            signature_blocks.append((item.get("Id"), item.get("Geometry")))

    # Extract form fields with key = "Signature"
    doc = Document(response)
    matched_fields = []
    for page in doc.pages:
        fields = page.form.searchFieldsByKey("Signature", ignoreCase=True)
        for field in fields:
            matched_fields.append((field.key, field.value))

    # Print results
    print("\n=== Detected Signature Blocks ===")
    print(tabulate(signature_blocks, headers=["Id", "Geometry"], tablefmt="grid", maxcolwidths=[None, 100]))

    print("\n=== Form Fields Matching 'Signature' ===")
    print(tabulate(matched_fields, headers=["Key", "Value"], tablefmt="grid"))

    return {
        "signatures": signature_blocks,
        "fields": matched_fields
    }
