"""
RAG 기능 동작 여부를 빠르게 검증하는 CLI 스크립트

실행 (프로젝트 루트에서):
  python agentic_system/scripts/test_rag.py
  python agentic_system/scripts/test_rag.py "트렌치코트 코디"
"""
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def main():
    from agentic_system.data_stores.rag import RAGStore

    query = sys.argv[1].strip() if len(sys.argv) > 1 else "오버사이즈란 뭐야?"
    print(f"[테스트] RAG 검색 쿼리: {query!r}\n")

    store = RAGStore(use_external=True, use_local=True)
    ctx = store.get_context("garment_recommendation", query)

    print("--- 내부(로컬) RAG 검색 결과 (rag_fashion_1gb + doc 등) ---")
    internal = ctx.get("rag_internal", [])
    for i, s in enumerate(internal[:5], 1):
        print(f"  {i}. {s[:200]}{'...' if len(s) > 200 else ''}")
    if not internal:
        print("  (없음)")

    print("\n--- 외부(웹) RAG 검색 결과 ---")
    external = ctx.get("rag_external", [])
    for i, s in enumerate(external[:3], 1):
        print(f"  {i}. {s[:200]}{'...' if len(s) > 200 else ''}")
    if not external:
        print("  (없음 - API 키/네트워크 확인)")

    print("\n--- 통합 rag_suggestions (최대 15개) ---")
    suggestions = ctx.get("rag_suggestions", [])
    print(f"  총 {len(suggestions)}개")
    for i, s in enumerate(suggestions[:5], 1):
        print(f"  {i}. {s[:180]}{'...' if len(s) > 180 else ''}")

    if internal or external or suggestions:
        print("\n[결과] RAG 기능 정상 동작 - 검색된 문맥이 API 응답 시 계획 강화에 사용됩니다.")
    else:
        print("\n[결과] 검색 결과 없음 - 로컬 데이터 경로/외부 API 설정을 확인하세요.")

if __name__ == "__main__":
    main()
