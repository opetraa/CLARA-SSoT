"""공용 파싱 데이터 구조 모델."""
# src/tractara/parsing/models.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BoundingBox:
    """PDF 좌표 정보"""

    x0: float
    y0: float
    x1: float
    y1: float
    page: int

    def to_dict(self) -> Dict[str, float]:
        """자신을 Dictionary로 변환합니다."""
        return {
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "page": self.page,
        }


@dataclass
class ParsedBlock:
    """단일 파싱 블록."""

    page: int
    block_type: str
    text: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    table_data: Optional[Dict] = None
    equation_data: Optional[Dict] = None
    confidence: float = 1.0
    # 계층 구조 필드
    level: int = 999  # 0: Title, 1: Section, 2+: Subsection, 999: Paragraph
    context_path: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    block_id: Optional[str] = None
    # 섹션 메타데이터
    section_label: Optional[str] = None  # 예: "1.2.3", "제2장"
    section_title: Optional[str] = None  # 번호 이후 제목 텍스트
    # 절차서 등에서 추출된 구조화된 엔지니어링 조건/파라미터 (schemas DOC_baseline 참조)
    structured_content: Optional[Dict[str, Any]] = None
    # 추적성 필드 (Phase 1, 3)
    source_xpath: Optional[str] = None
    source_element_name: Optional[str] = None
    xml_fragment: Optional[str] = None


@dataclass
class ParsedDocument:
    """파싱된 전체 문서 컨테이너."""

    source_path: str
    blocks: List[ParsedBlock]
    metadata: Optional[Dict] = None
    # 문서 전체의 교차 참조 정보 (sourceBlockId, relationType, target 등을 담음)
    relations: List[Dict[str, Any]] = field(default_factory=list)
    # Fragment Store 저장을 위한 원본 XML 조각들 (block_id -> xml_string)
    xml_fragments: Dict[str, str] = field(default_factory=dict)
