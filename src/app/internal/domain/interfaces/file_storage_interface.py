from abc import ABC, abstractmethod

class IFileStorage(ABC):

    @abstractmethod
    def upload(self, *, object_key: str, file_bytes: bytes, content_type: str) -> None:
        ...

    @abstractmethod
    def delete(self, *, object_key: str) -> None:
        ...