# src/clara_ssot/parsing/pdf_parser.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ParsedBlock:
    page: int
    block_type: str  # "text" | "table" | "image" | "ocr"
    text: Optional[str] = None


@dataclass
class ParsedDocument:
    source_path: str
    blocks: List[ParsedBlock]


def parse_pdf(path: Path) -> ParsedDocument:
    """
    진짜 PDF 파싱은 나중에,
    지금은 흐름만 확인하는 더미 구현.

    나중에 여기서 pdfplumber / pymupdf / OCR 등을 붙이면 됨.
    """
    dummy_block = ParsedBlock(
        page=1,
        block_type="text",
        text="Dummy text extracted from PDF",
    )
    return ParsedDocument(source_path=str(path), blocks=[dummy_block])
