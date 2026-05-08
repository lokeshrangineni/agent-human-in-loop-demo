"""Convert PDF documents to base64-encoded page images for vision LLM input."""

import base64
import io
import logging
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_DPI = 200
MAX_DIMENSION = 2048


def pdf_to_images_b64(file_path: str | Path, dpi: int = DEFAULT_DPI) -> list[str]:
    """
    Convert each page of a PDF to a base64-encoded PNG image.

    Args:
        file_path: Path to the PDF file.
        dpi: Resolution for rendering. Higher = better quality but larger payload.

    Returns:
        List of base64-encoded PNG strings (one per page).
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    images_b64 = []
    doc = fitz.open(str(file_path))

    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = _constrain_size(img, MAX_DIMENSION)

            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            images_b64.append(b64)

            logger.info(
                "Converted page %d/%d: %dx%d, %.1f KB",
                page_num + 1, len(doc),
                img.width, img.height,
                len(b64) * 3 / 4 / 1024,
            )
    finally:
        doc.close()

    return images_b64


def image_file_to_b64(file_path: str | Path) -> list[str]:
    """Convert an image file (PNG, JPG, etc.) to a single base64-encoded string."""
    file_path = Path(file_path)
    img = Image.open(file_path).convert("RGB")
    img = _constrain_size(img, MAX_DIMENSION)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    logger.info(
        "Converted image: %dx%d, %.1f KB",
        img.width, img.height,
        len(b64) * 3 / 4 / 1024,
    )
    return [b64]


def document_to_images_b64(file_path: str | Path) -> list[str]:
    """Auto-detect file type and convert to base64 images."""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return pdf_to_images_b64(file_path)
    elif suffix in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"):
        return image_file_to_b64(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _constrain_size(img: Image.Image, max_dim: int) -> Image.Image:
    """Resize if either dimension exceeds max_dim, preserving aspect ratio."""
    if img.width <= max_dim and img.height <= max_dim:
        return img

    if img.width > img.height:
        new_w = max_dim
        new_h = int(img.height * max_dim / img.width)
    else:
        new_h = max_dim
        new_w = int(img.width * max_dim / img.height)

    return img.resize((new_w, new_h), Image.LANCZOS)
