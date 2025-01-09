from enum import Enum


class ErrorCode(Enum):
    GET_PROFILES_ERROR = ("ERR001", "Error getting profiles")

    def __init__(self, code, message):
        self.code = code
        self.message = message

    @classmethod
    def get_message(cls, code):
        for error in cls:
            if error.code == code:
                return error.message
        return "Unknown error"
