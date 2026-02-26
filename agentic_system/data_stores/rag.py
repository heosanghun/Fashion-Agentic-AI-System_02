"""
RAG (Retrieval-Augmented Generation) Store

- 외부(인터넷): 웹 검색 RAG (ExternalRAG)
- 내부(임시 로컬): 로컬 문서 디렉터리 기반 RAG (LocalRAG)
- Mock: 규칙/키워드 기반 (MockRAG)
"""

from typing import Dict, List, Optional, Any
import json

try:
    from .rag_external import ExternalRAG
except ImportError:
    ExternalRAG = None
try:
    from .rag_local import LocalRAG
except ImportError:
    LocalRAG = None


class MockRAG:
    """
    Mock RAG Store
    
    PoC 단계에서 사용하는 단순한 규칙/데이터 기반 RAG
    실제 RAG 파이프라인 대신 JSON 데이터 사용
    """
    
    def __init__(self):
        self.knowledge_base = self._init_knowledge_base()
        self.name = "MockRAG"
    
    def _init_knowledge_base(self) -> Dict[str, Any]:
        """Mock 지식 베이스 초기화"""
        return {
            "garment_types": {
                "상의": ["후드티", "티셔츠", "셔츠", "블라우스"],
                "하의": ["바지", "청바지", "스커트", "반바지"],
                "아우터": ["재킷", "코트", "패딩", "바람막이"]
            },
            "styles": {
                "스트리트": "오버사이즈, 힙합, 그래피티 스타일",
                "캐주얼": "편안한 일상 복장, 데일리 룩",
                "포멀": "정장, 비즈니스 캐주얼",
                "스포츠": "운동복, 활동적인 스타일"
            },
            "materials": {
                "면": "통기성 좋음, 세탁 쉬움",
                "폴리에스터": "구김 적음, 빠른 건조",
                "데님": "내구성 좋음, 캐주얼 스타일"
            },
            "color_guidelines": {
                "검정색": "모든 스타일과 어울림, 슬림하게 보임",
                "흰색": "깔끔한 느낌, 여름에 적합",
                "회색": "중성적, 다양한 색상과 매칭 가능"
            }
        }
    
    def retrieve(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        지식 검색
        
        Args:
            query: 검색 쿼리
            context: 추가 컨텍스트
            
        Returns:
            Dict: 검색된 지식 정보
        """
        query_lower = query.lower()
        results = {
            "suggestions": [],
            "relevant_info": {},
            "confidence": 0.0
        }
        
        # 간단한 키워드 매칭
        for category, data in self.knowledge_base.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    if query_lower in key.lower() or query_lower in str(value).lower():
                        results["suggestions"].append({
                            "category": category,
                            "key": key,
                            "value": value
                        })
                        results["relevant_info"][category] = data
        
        # 신뢰도 계산
        if results["suggestions"]:
            results["confidence"] = min(1.0, len(results["suggestions"]) / 5.0)
        
        return results
    
    def get_rag_context(self, plan_type: str, user_input: str) -> Dict[str, Any]:
        """
        RAG 컨텍스트 생성
        
        Agent 2에게 전달할 RAG 컨텍스트 생성
        """
        if plan_type == "3d_generation":
            # 3D 생성에 필요한 정보
            results = self.retrieve(user_input)
            return {
                "rag_suggestions": results.get("suggestions", []),
                "garment_info": results.get("relevant_info", {}),
                "confidence": results.get("confidence", 0.0)
            }
        elif plan_type == "garment_recommendation":
            # 추천에 필요한 정보
            results = self.retrieve(user_input)
            return {
                "rag_suggestions": results.get("suggestions", []),
                "style_info": results.get("relevant_info", {}).get("styles", {}),
                "confidence": results.get("confidence", 0.0)
            }
        else:
            return {
                "rag_suggestions": [],
                "confidence": 0.0
            }


class RAGStore:
    """
    RAG Store — 외부(인터넷) + 내부(임시 로컬) 이중 RAG
    
    - external: 웹 검색 (DuckDuckGo 또는 Serper API)
    - internal: 로컬 doc/ 및 data/local_rag_docs/ 문서 검색
    - mock: 규칙 기반 패션 지식 (기존 MockRAG)
    """
    
    def __init__(self, vector_db_type: str = "chroma", use_external: bool = True, use_local: bool = True):
        self.vector_db_type = vector_db_type
        self.mock_rag = MockRAG()
        self.external_rag = ExternalRAG(max_results=5) if use_external and ExternalRAG else None
        self.local_rag = LocalRAG() if use_local and LocalRAG else None
    
    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """지식 검색 (Mock 기준, 하위 호환)"""
        return self.mock_rag.retrieve(query)
    
    def get_context(self, plan_type: str, user_input: str) -> Dict[str, Any]:
        """
        외부 + 내부 RAG를 모두 조회해 하나의 RAG 컨텍스트로 합침.
        사용자 입력(user_input)으로 정보를 찾을 수 있도록 함.
        """
        if not user_input or not user_input.strip():
            return self.mock_rag.get_rag_context(plan_type, user_input)
        
        query = user_input.strip()
        all_suggestions: List[Any] = []
        internal_suggestions: List[str] = []
        external_suggestions: List[str] = []
        
        # 1) 내부(로컬) RAG
        if self.local_rag:
            try:
                ctx = self.local_rag.get_context(query, top_k=5)
                internal_suggestions = ctx.get("suggestions", [])
                for s in internal_suggestions:
                    all_suggestions.append({"source": "internal", "text": s[:500]})
            except Exception as e:
                print(f"[RAGStore] 내부 RAG 오류: {e}")
        
        # 2) 외부(인터넷) RAG
        if self.external_rag:
            try:
                ctx = self.external_rag.get_context(query, max_results=5)
                external_suggestions = ctx.get("suggestions", [])
                for s in external_suggestions:
                    all_suggestions.append({"source": "external", "text": s[:500]})
            except Exception as e:
                print(f"[RAGStore] 외부 RAG 오류: {e}")
        
        # 3) Mock RAG (패션 키워드 보강)
        mock_ctx = self.mock_rag.get_rag_context(plan_type, user_input)
        mock_suggestions = mock_ctx.get("rag_suggestions", [])
        for s in mock_suggestions:
            if isinstance(s, dict):
                all_suggestions.append({"source": "mock", "text": str(s.get("value", s))[:300]})
            else:
                all_suggestions.append({"source": "mock", "text": str(s)[:300]})
        
        # F.LLM / Agent 2 에서 쓰는 형식 (문자열 목록)
        mock_str = [str(s.get("value", s))[:300] if isinstance(s, dict) else str(s)[:300] for s in mock_suggestions]
        rag_suggestions = internal_suggestions + external_suggestions + mock_str
        return {
            "rag_suggestions": rag_suggestions[:15],
            "rag_internal": internal_suggestions[:5],
            "rag_external": external_suggestions[:5],
            "rag_mock": mock_ctx,
            "confidence": mock_ctx.get("confidence", 0.0),
        }

