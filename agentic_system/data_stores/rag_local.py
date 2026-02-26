"""
내부 RAG — 임시 로컬 문서 기반 검색

지정 디렉터리의 .txt, .md 파일을 로드해 청크 단위로 보관하고,
사용자 질의와 키워드/문자열 매칭으로 관련 문단 검색
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import re

# 기본 로컬 문서 디렉터리 (프로젝트 내)
_AGENTIC_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DOCS_DIR = _AGENTIC_ROOT.parent / "doc"  # 프로젝트 루트 doc
_LOCAL_RAG_DIR = _AGENTIC_ROOT / "data" / "local_rag_docs"  # agentic_system/data/local_rag_docs
_RAG_FASHION_1GB_DIR = _AGENTIC_ROOT / "data" / "rag_fashion_1gb"  # 패션 RAG 1GB 수집 폴더


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """텍스트를 고정 길이 청크로 자르기 (문장 경계 우선)"""
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # 문장 경계 찾기
            for sep in (". ", ".\n", "? ", "! ", "\n\n"):
                idx = text.rfind(sep, start, end + 1)
                if idx != -1:
                    end = idx + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if overlap < end - start else end
    return chunks


class LocalRAG:
    """
    내부(임시 로컬) RAG: 로컬 디렉터리의 문서를 로드해 검색
    """
    def __init__(self, docs_dir: Optional[Path] = None, chunk_size: int = 500):
        self.docs_dir = Path(docs_dir) if docs_dir else _LOCAL_RAG_DIR
        self.chunk_size = chunk_size
        self._chunks: List[Dict[str, Any]] = []  # { "text", "source", "chunk_id" }
        self._load_documents()

    def _load_documents(self) -> None:
        """docs_dir, rag_fashion_1gb, 프로젝트 doc 폴더에서 .txt, .md 로드 후 청크화"""
        self._chunks = []
        seen = set()
        for base_dir in (self.docs_dir, _RAG_FASHION_1GB_DIR, _DEFAULT_DOCS_DIR):
            if not base_dir.exists():
                continue
            for path in base_dir.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in (".txt", ".md"):
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    print(f"[LocalRAG] 파일 읽기 실패 {path}: {e}")
                    continue
                try:
                    source = str(path.relative_to(base_dir))
                except ValueError:
                    source = path.name
                for i, chunk in enumerate(_chunk_text(text, self.chunk_size)):
                    key = (source, i)
                    if key in seen:
                        continue
                    seen.add(key)
                    self._chunks.append({
                        "text": chunk,
                        "source": source,
                        "chunk_id": len(self._chunks),
                    })
        print(f"[LocalRAG] 로드된 청크 수: {len(self._chunks)} (디렉터리: {self.docs_dir}, {_RAG_FASHION_1GB_DIR}, {_DEFAULT_DOCS_DIR})")

    def add_document(self, text: str, source: str = "user") -> None:
        """문서 한 건 추가 (임시 로컬 확장용)"""
        for i, chunk in enumerate(_chunk_text(text, self.chunk_size)):
            self._chunks.append({
                "text": chunk,
                "source": source,
                "chunk_id": len(self._chunks),
            })

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        키워드/문자열 매칭으로 관련 청크 반환
        """
        if not query or not self._chunks:
            return []
        q_lower = query.lower()
        q_words = set(re.findall(r"\w+", q_lower))
        scored = []
        for c in self._chunks:
            text = c["text"]
            t_lower = text.lower()
            score = 0.0
            if q_lower in t_lower:
                score += 2.0
            for w in q_words:
                if len(w) < 2:
                    continue
                if w in t_lower:
                    score += 1.0
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        return [c for _, c in scored[:top_k]]

    def get_context(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        검색 결과를 RAG 컨텍스트 형식으로 반환
        """
        hits = self.search(query, top_k=top_k)
        suggestions = [h["text"] for h in hits]
        return {
            "source": "internal",
            "query": query,
            "hits": hits,
            "suggestions": suggestions,
            "count": len(hits),
        }

    def reload(self) -> None:
        """문서 디렉터리 다시 로드"""
        self._load_documents()
