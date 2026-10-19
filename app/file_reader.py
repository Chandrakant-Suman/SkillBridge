"""Turn an uploaded resume or job description (PDF or .txt) into clean text.

Everything happens in memory: files are never saved to disk.
"""
import re

import pymupdf

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MIN_TEXT_CHARS = 50  # less than this usually means a scanned/image-only PDF

# Control characters and the "unknown glyph" mark that PDF icons (phone, email) turn into.
_JUNK_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]|\N{REPLACEMENT CHARACTER}")


class DocumentError(ValueError):
    """Raised when an uploaded file can't be turned into usable text."""


def normalize_text(text: str) -> str:
    text = text.replace("\N{NO-BREAK SPACE}", " ")
    text = _JUNK_CHARS.sub(" ", text)
    text = re.sub(r"[ \t]+", " ", text)         # collapse runs of spaces/tabs
    text = re.sub(r"\n\s*\n+", "\n\n", text)    # collapse blank lines
    return text.strip()


def _read_pdf(data: bytes) -> str:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            if document.needs_pass:
                raise DocumentError("Password-protected PDFs are not supported.")
            return "\n".join(page.get_text() for page in document)
    except DocumentError:
        raise
    except Exception as exc:  # corrupted / truncated PDF
        raise DocumentError("The PDF could not be read. It may be corrupted.") from exc


def _read_txt(data: bytes) -> str:
    if b"\x00" in data:  # real text files never contain NUL bytes; binaries (.docx, images) do
        raise DocumentError("This doesn't look like a plain-text file.")
    for encoding in ("utf-8-sig", "cp1252"):  # UTF-8 first, then Windows Notepad's old default
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise DocumentError("Unsupported text encoding. Please save the file as UTF-8.")


def read_document(data: bytes, filename: str) -> str:
    """Return clean text from a PDF or .txt upload, or raise DocumentError."""
    if not data:
        raise DocumentError(f"{filename} is empty.")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise DocumentError(f"{filename} is larger than the 5 MB limit.")

    # Decide by CONTENT for PDFs (magic bytes), not by trusting the extension.
    if data[:5] == b"%PDF-":
        raw = _read_pdf(data)
    elif filename.lower().endswith(".txt"):
        raw = _read_txt(data)
    else:
        raise DocumentError(f"{filename} must be a PDF or a .txt file.")

    text = normalize_text(raw)
    if len(text) < MIN_TEXT_CHARS:
        raise DocumentError(
            f"Very little text was found in {filename}. If it is a scanned image, "
            "please upload a text-based PDF or a .txt file."
        )
    return text
