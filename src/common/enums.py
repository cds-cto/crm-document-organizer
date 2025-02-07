from enum import Enum


class AccountNumType(Enum):
    LAST4 = "last4"
    LAST12 = "last12"
    LAST16 = "last16"

class UnMappedDocumentStatus(Enum):
    UPLOADED = 0
    PROCESSING = 1
    PENDING = 2
    TRANSFERRED = 3
    UNKNOWN = 4