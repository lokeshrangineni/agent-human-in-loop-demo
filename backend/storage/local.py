import aiofiles
from pathlib import Path

from backend.config import UPLOAD_DIR
from backend.storage.base import DocumentStore


class LocalDocumentStore(DocumentStore):
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or UPLOAD_DIR

    def _get_dir(self, file_id: str) -> Path:
        if ".." in file_id or "/" in file_id or "\\" in file_id:
            raise ValueError(f"Invalid file_id: {file_id}")
        d = self.base_dir / file_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    async def upload(self, file_id: str, content: bytes, filename: str) -> str:
        file_dir = self._get_dir(file_id)
        suffix = Path(filename).suffix
        file_path = file_dir / f"original{suffix}"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return str(file_path)

    async def download(self, file_id: str) -> bytes:
        file_dir = self._get_dir(file_id)
        originals = list(file_dir.glob("original.*"))
        if not originals:
            raise FileNotFoundError(f"No document found for {file_id}")
        async with aiofiles.open(originals[0], "rb") as f:
            return await f.read()

    async def get_path(self, file_id: str) -> str:
        file_dir = self._get_dir(file_id)
        originals = list(file_dir.glob("original.*"))
        if not originals:
            raise FileNotFoundError(f"No document found for {file_id}")
        return str(originals[0])

    async def delete(self, file_id: str) -> None:
        if ".." in file_id or "/" in file_id or "\\" in file_id:
            raise ValueError(f"Invalid file_id: {file_id}")
        file_dir = self.base_dir / file_id
        if file_dir.exists():
            import shutil
            shutil.rmtree(file_dir)

    async def exists(self, file_id: str) -> bool:
        if ".." in file_id or "/" in file_id or "\\" in file_id:
            return False
        file_dir = self.base_dir / file_id
        return file_dir.exists() and any(file_dir.glob("original.*"))
