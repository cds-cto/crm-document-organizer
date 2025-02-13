from enum import Enum


class AccountNumType(Enum):
    LAST4 = "last4"
    LAST12 = "last12"
    LAST16 = "last16"

class UnMappedDocumentStatus(Enum):
    PENDING = 0
    UPLOADED = 1
    TRANSFERRED = 2
    UNKNOWN = 3