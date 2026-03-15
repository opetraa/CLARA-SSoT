"""Fragment Store (원본 XML 조각 저장소) 모듈."""
# src/tractara/ssot/fragment_store.py
import json
from pathlib import Path
from typing import Dict, Optional, Protocol


class FragmentStore(Protocol):
    def put(self, block_id: str, xml_fragment: str) -> None:
        ...

    def get(self, block_id: str) -> Optional[str]:
        ...

    def bulk_put(self, fragments: Dict[str, str]) -> None:
        ...


# LLM과 RAG 엔진이 읽어야 할 SSoT JSON은 극도로 가볍고 순수하게 유지되며, 마이그레이션 모듈은 필요할 때만 O(1)의 속도로 원본 조각을 꺼내 쓸 수 있게
class FileFragmentStore:
    """파일 기반 JSON K-V 저장소 (향후 Redis 전환 대비)"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, block_id: str) -> Path:
        # 안전한 파일명 생성
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in block_id)
        return self.base_dir / f"{safe_id}.json"

    def put(self, block_id: str, xml_fragment: str) -> None:
        path = self._get_path(block_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"blockId": block_id, "xmlFragment": xml_fragment},
                f,
                ensure_ascii=False,
            )

    def get(self, block_id: str) -> Optional[str]:
        path = self._get_path(block_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("xmlFragment")
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def bulk_put(self, fragments: Dict[str, str]) -> None:
        for block_id, xml_fragment in fragments.items():
            if xml_fragment:
                self.put(block_id, xml_fragment)


class RedisFragmentStore:
    """추후 Redis 전환용 Stub"""

    def __init__(self, redis_url: str):
        pass

    def put(self, block_id: str, xml_fragment: str) -> None:
        raise NotImplementedError("Redis store not yet implemented")

    def get(self, block_id: str) -> Optional[str]:
        raise NotImplementedError("Redis store not yet implemented")

    def bulk_put(self, fragments: Dict[str, str]) -> None:
        raise NotImplementedError("Redis store not yet implemented")
