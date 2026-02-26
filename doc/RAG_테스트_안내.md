# RAG 기능 테스트 안내

로컬 RAG(40.85MB 패션 데이터)가 실제로 검색·계획 강화에 쓰이는지 확인하는 방법입니다.

---

## 1. CLI로 RAG만 빠르게 검증 (권장)

백엔드/프론트 없이 **RAG 검색만** 동작하는지 확인할 때 사용합니다.

**실행 (프로젝트 루트에서):**

```powershell
cd "d:\AI\Fashion-Agentic-AI-System_01"
python agentic_system\scripts\test_rag.py
```

기본 쿼리: `"오버사이즈란 뭐야?"`

**쿼리 직접 지정:**

```powershell
python agentic_system\scripts\test_rag.py "트렌치코트 코디"
python agentic_system\scripts\test_rag.py "데님 소재 특징"
```

**정상이면:**

- `[LocalRAG] 로드된 청크 수: 109537 (... rag_fashion_1gb, ...)` 같은 로그가 보이고
- "내부(로컬) RAG 검색 결과"에 위키/큐레이션에서 나온 문장들이 출력되며
- 마지막에 `[결과] RAG 기능 정상 동작` 이 나옵니다.

---

## 2. 백엔드 + 프론트에서 통합 테스트

실제 API·UI 흐름에서 RAG가 쓰이는지 확인하려면 아래 순서로 실행합니다.

### 2.1 백엔드 실행

```powershell
cd "d:\AI\Fashion-Agentic-AI-System_01"
python -m agentic_system.api.main
```

또는 (api 폴더에서):

```powershell
cd "d:\AI\Fashion-Agentic-AI-System_01\agentic_system\api"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**RAG 관련 로그 확인:**

- 서버 기동 시: `[LocalRAG] 로드된 청크 수: N (..., rag_fashion_1gb, ...)` → 로컬 RAG 로드됨
- 요청 시: `[RAGStore] 내부 RAG 오류` 가 없으면 내부 RAG는 정상

### 2.2 프론트 실행

```powershell
cd "d:\AI\Fashion-Agentic-AI-System_01\agentic_system\frontend"
npm install
npm run dev
```

브라우저에서 표시되는 주소(예: http://localhost:5173)로 접속합니다.

### 2.3 테스트할 질문 예시

RAG가 쓰이기 좋은 질문(로컬 문서에 있는 키워드):

| 질문 | 기대 |
|------|------|
| 오버사이즈란 뭐야? | 로컬 큐레이션/위키에서 설명 문장 검색 후 계획·응답에 반영 |
| 트렌치코트 코디 추천해줘 | 트렌치코트 관련 문맥 검색 후 추천 계획에 사용 |
| 데님 소재 특징 알려줘 | 소재·데님 관련 문단 검색 |
| 패션 용어 하이웨이스트 설명해줘 | 큐레이션/위키에서 하이웨이스트 설명 검색 |

**확인 방법:**

- 백엔드 터미널에 `[RAGStore] 내부 RAG 오류` 가 없고, 위와 같은 질문에 응답이 오면 RAG 경로는 통과한 것입니다.
- 현재 PoC는 **규칙 기반** 계획 생성이라, RAG 검색 결과는 `rag_suggestions`로 계획 강화(`_enhance_with_rag`)에만 쓰이고, 응답 문장이 곧바로 “위키 인용” 형태로 나오지는 않을 수 있습니다. 다만 RAG가 호출되고 검색된 문맥이 계획에 반영되는지 확인하려면 1번 CLI 테스트가 가장 확실합니다.

---

## 3. 요약

| 방법 | 목적 |
|------|------|
| **CLI** `python agentic_system\scripts\test_rag.py [쿼리]` | RAG 검색·로컬 데이터 반영 여부만 빠르게 검증 |
| **백엔드 + 프론트** | API·UI 전체 흐름에서 RAG 호출 및 오류 여부 확인 |

RAG가 “구현되어 동작하는지” 확인하려면 **1번 CLI 테스트**를 한 번 실행해 보시면 됩니다.
