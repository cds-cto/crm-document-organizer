import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
# Load key and IV
key = base64.b64decode("tzyfoL6++PNjDbw70yJ1akZQnD0swannopGt+RAgPck=")
iv = base64.b64decode("/iQfiFFipwqY6eoTcAOPsw==")


def encrypt(original: str) -> str:
    # Convert string to bytes
    plain_bytes = original.encode('utf-8')
    
    # PKCS7 padding (manual, to match .NET behavior)
    block_size = 16
    pad_len = block_size - len(plain_bytes) % block_size
    padded = plain_bytes + bytes([pad_len] * pad_len)
    
    # AES CBC encryption
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_bytes = encryptor.update(padded) + encryptor.finalize()
    
    # Return as base64 string
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def decrypt(encrypted_b64: str) -> str:
    # Decode the base64-encoded string
    encrypted_bytes = base64.b64decode(encrypted_b64)

    # AES CBC decryption
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(encrypted_bytes) + decryptor.finalize()

    # Remove PKCS7 padding
    padding_len = padded_plaintext[-1]
    plaintext_bytes = padded_plaintext[:-padding_len]

    return plaintext_bytes.decode('utf-8')
