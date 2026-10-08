"""OWNER: ALL - shared exceptions"""
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, what: str = "Resource"):
        super().__init__(status.HTTP_404_NOT_FOUND, f"{what} not found")


class InvalidTransitionError(HTTPException):
    def __init__(self, old: str, new: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, f"Invalid status transition: {old} -> {new}")


class DuplicateError(HTTPException):
    def __init__(self, msg: str = "A similar active record already exists"):
        super().__init__(status.HTTP_409_CONFLICT, msg)
