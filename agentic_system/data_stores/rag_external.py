"""
외부 RAG — 인터넷 검색 (웹) 기반 정보 검색

API 키 없이 사용 가능: duckduckgo-search (pip install duckduckgo-search)
선택: SERPER_API_KEY 있으면 Serper(Google) 검색 사용
"""

from typing import Dict, List, Any, Optional
import os

# duckduckgo-search (선택, pip install duckduckgo-search)
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class ExternalRAG:
    """
    외부(인터넷) RAG: 웹 검색으로 사용자 질의와 관련된 정보 조회
    """
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self._serper_key = (os.environ.get("SERPER_API_KEY") or "").strip()

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        쿼리로 웹 검색 후 스니펫·제목·URL 목록 반환
        """
        k = max_results or self.max_results
        results: List[Dict[str, Any]] = []

        # 1) Serper API (Google 검색, API 키 필요)
        if self._serper_key and query:
            try:
                import requests
                r = requests.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": self._serper_key, "Content-Type": "application/json"},
                    json={"q": query, "num": k},
                    timeout=8,
                )
                if r.status_code == 200:
                    data = r.json()
                    for item in (data.get("organic") or [])[:k]:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "url": item.get("link", ""),
                            "source": "serper",
                        })
                    return results
            except Exception as e:
                print(f"[ExternalRAG] Serper 검색 실패: {e}")

        # 2) DuckDuckGo (API 키 불필요)
        if DDGS_AVAILABLE and query:
            try:
                with DDGS() as ddgs:
                    for row in ddgs.text(query, max_results=k):
                        results.append({
                            "title": row.get("title", ""),
                            "snippet": row.get("body", ""),
                            "url": row.get("href", ""),
                            "source": "duckduckgo",
                        })
                return results
            except Exception as e:
                print(f"[ExternalRAG] DuckDuckGo 검색 실패: {e}")

        return results

    def get_context(self, query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
        """
        검색 결과를 RAG 컨텍스트 형식으로 반환
        """
        hits = self.search(query, max_results=max_results)
        suggestions = [
            f"[{h['title']}] {h['snippet']}" if h.get("snippet") else h.get("title", "")
            for h in hits
        ]
        return {
            "source": "external",
            "query": query,
            "hits": hits,
            "suggestions": suggestions,
            "count": len(hits),
        }
