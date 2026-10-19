import pytest

from app.file_reader import DocumentError, normalize_text, read_document
from tests.conftest import SAMPLE_RESUME, make_pdf


def test_reads_pdf():
    text = read_document(make_pdf(SAMPLE_RESUME), "resume.pdf")
    assert "Python" in text and "Projects" in text


def test_reads_utf8_txt():
    text = read_document(SAMPLE_RESUME.encode("utf-8"), "jd.txt")
    assert "MongoDB" in text


def test_reads_windows_notepad_txt():
    data = (SAMPLE_RESUME + "Café – naïve").encode("cp1252")
    assert "Café" in read_document(data, "jd.txt")


def test_rejects_fake_pdf():
    with pytest.raises(DocumentError, match="PDF or a .txt"):
        read_document(b"I am not really a PDF file, just text " * 3, "resume.pdf")


def test_rejects_other_file_types():
    with pytest.raises(DocumentError, match="PDF or a .txt"):
        read_document(b"PK\x03\x04 pretend docx" * 10, "resume.docx")


def test_rejects_binary_renamed_to_txt():
    with pytest.raises(DocumentError, match="plain-text"):
        read_document(b"\x89PNG\x00\x00 binary data" * 10, "jd.txt")


def test_rejects_empty_file():
    with pytest.raises(DocumentError, match="empty"):
        read_document(b"", "resume.pdf")


def test_rejects_pdf_without_text():
    with pytest.raises(DocumentError, match="Very little text"):
        read_document(make_pdf(" "), "resume.pdf")


def test_rejects_corrupted_pdf():
    with pytest.raises(DocumentError, match="corrupted"):
        read_document(b"%PDF-1.7\n garbage garbage garbage", "resume.pdf")


def test_rejects_too_large():
    with pytest.raises(DocumentError, match="5 MB"):
        read_document(b"a" * (5 * 1024 * 1024 + 1), "jd.txt")


def test_normalize_text():
    assert normalize_text("a   b\t\tc\n\n\n\nd") == "a b c\n\nd"
