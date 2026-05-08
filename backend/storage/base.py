from abc import ABC, abstractmethod


class DocumentStore(ABC):
    @abstractmethod
    async def upload(self, file_id: str, content: bytes, filename: str) -> str:
        """Store a document and return its storage path."""
        ...

    @abstractmethod
    async def download(self, file_id: str) -> bytes:
        """Retrieve document content by file ID."""
        ...

    @abstractmethod
    async def get_path(self, file_id: str) -> str:
        """Get the local/URL path for a document."""
        ...

    @abstractmethod
    async def delete(self, file_id: str) -> None:
        """Delete a document."""
        ...

    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        """Check if a document exists."""
        ...
