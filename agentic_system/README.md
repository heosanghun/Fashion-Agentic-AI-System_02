# Fashion Agentic AI System — 에이전트 코어

패션 Agentic AI 가상 피팅 POC의 **핵심 에이전트 시스템**입니다.  
**21가지 Agent Design Patterns** 중 **5가지**를 적용해 구현했습니다.

---

## 아키텍처 개요

- **인식(Perception)** → **판단(Judgment)** → **행동(Action)** 3단계
- **Agent 1 (Agent Runtime)**: 오케스트레이션, 의도 분석, 추상 계획, 도구 실행, 자기 수정 루프
- **Agent 2 (F.LLM)**: 추상 계획 → 구체적 실행 계획(JSON), RAG 보강
- **RAG**: 로컬(doc/, rag_fashion_1gb) + 외부(웹) + Mock
- **도구**: Gemini Try-On, 상품 검색(Mock)

---

## 적용된 5가지 디자인 패턴

| 패턴 | 구현 위치 |
|------|-----------|
| 프롬프트 체이닝 | f_llm 실행 단계 생성 → agent_runtime 순차 실행 |
| 라우팅 | agent_runtime._analyze_user_intent, _create_abstract_plan |
| 도구 사용 | agent_runtime.tools_registry, _execute_plan |
| 반성 | agent_runtime._evaluate_result |
| 복구 | agent_runtime._self_correction_loop (최대 1회 재시도) |

---

## 디렉토리 구조

```
agentic_system/
├── api/
│   └── main.py              # FastAPI, /api/v1/request, 세션/파일 API
├── core/
│   ├── agent_runtime.py     # Agent 1
│   ├── f_llm.py             # Agent 2
│   ├── memory.py            # ShortTermMemory
│   └── custom_ui.py         # Payload·결과 포맷
├── tools/
│   ├── gemini_tryon.py      # 가상 피팅 (Gemini API)
│   └── functions.py        # 상품 검색
├── data_stores/
│   ├── rag.py               # RAG 통합
│   ├── rag_local.py         # 로컬 RAG
│   ├── rag_external.py     # 외부 웹 RAG
│   └── rag_vector.py       # Vector RAG (향후)
├── models/
│   └── internvl2_wrapper.py # InternVL2 래퍼 (선택)
├── data/
│   ├── local_rag_docs/
│   └── rag_fashion_1gb/
├── scripts/
│   ├── collect_fashion_rag_data.py
│   ├── verify_rag_1gb.py
│   └── test_rag.py
├── frontend/                # React + Vite
└── requirements.txt
```

---

## 설치 및 실행

```bash
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

프론트엔드:

```bash
cd frontend && npm install && npm run dev
```

---

## 참고

- 루트 [README.md](../README.md): 전체 프로젝트 개요, 5가지 패턴 표, 디렉토리 구조
- doc/코드_및_디렉토리_구조_가이드.md: 파일별 기능·작동 원리
