# 👗 Fashion Agentic AI System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**패션 Agentic AI 가상 피팅 POC — 21가지 디자인 패턴 중 5가지 적용**

[개요](#-프로젝트-정의) • [5가지 패턴](#-현재-poc-적용-5가지-디자인-패턴) • [디렉토리 구조](#-디렉토리-구조) • [설치](#-설치-방법) • [사용법](#-사용-방법)

</div>

---

## 📋 프로젝트 정의

**Fashion Agentic AI System**은 **Google 등에서 검증된 21개 Agent Design Patterns**를 기반으로 한 **Agentic AI 가상 피팅 POC**입니다.

현재 PoC 단계에서는 21개 중 **5가지 핵심 패턴**만 적용해 구현했으며, 지능형 에이전트가 사용자 의도를 인식하고, 계획을 판단하며, 도구를 자율 실행하는 **인식 → 판단 → 행동** 프로세스를 검증합니다.

### 핵심 목표

1. **에이전트 기반 오케스트레이션**: 인식·판단·행동 3단계와 Agent 1·Agent 2 협업
2. **5대 디자인 패턴 구현**: 프롬프트 체이닝, 라우팅, 도구 사용, 반성, 복구
3. **RAG 활용**: 로컬·외부·Mock RAG로 판단 정확도 보강
4. **가상 피팅**: Gemini API 기반 Try-On 도구 연동

### 기술적 특징

- **Agentic AI**: "인식(Perception) → 판단(Judgment) → 행동(Action)" 3단계
- **멀티 에이전트**: Agent 1 (Agent Runtime) + Agent 2 (F.LLM)
- **ADK 미사용**: 자체 구현 오케스트레이션 (LangChain/LlamaIndex 미사용)
- **가상 피팅 도구**: Google Gemini API 기반 의류 분석·Try-On

---

## ✨ 현재 POC 적용 5가지 디자인 패턴

본 프로젝트는 **21개 Agent Design Patterns** 중 아래 **5가지를 코드로 구현**했습니다.

| 번호 | 패턴 | 의미 | 이 프로젝트에서의 구현 |
|------|------|------|------------------------|
| 1 | **프롬프트 체이닝** | 복잡한 작업을 여러 단계로 나누어 순차 처리 | 추상 계획 → 실행 계획(JSON) → 단계별 도구 순차 실행 |
| 2 | **라우팅** | 사용자 입력에 따라 다음 경로를 동적으로 결정 | 의도 분석(3D 생성/의류 추천/대화/정보 검색) 후 해당 플로우로 분기 |
| 3 | **도구 사용** | 외부 API·함수를 호출해 실제 작업 수행 | Agent Runtime이 gemini_tryon, 상품 검색 등 등록 도구를 순차 호출 |
| 4 | **반성** | 결과를 스스로 검증·평가 | 실행 결과를 _evaluate_result로 검사해 성공/실패 판단 |
| 5 | **복구** | 오류 시 재시도로 시스템 정지 방지 | 실패 시 최대 1회 _execute_plan 재실행(자기 수정 루프) |

**나머지 16개 패턴**은 문서에 정의되어 있으며 Pilot 1·2 단계에서 점진 도입 예정입니다. (병렬화, 계획, 다중 에이전트 협업, RAG 고도화, 메모리 관리, 가드레일, A2A, MCP 등)

---

## 💡 작동 원리

### 전체 흐름

```
[사용자 입력 (텍스트 + 이미지)]
    ↓
[프론트엔드 (React)]
    ↓
[API 서버 (FastAPI)]
    ↓
[Agent Runtime (Agent 1)]
    ├─ 인식: 의도 분석 (3D 생성 / 의류 추천 / 대화 / 정보 검색)
    ├─ 판단: 추상 계획 수립 → RAG 검색 → Agent 2에게 전달
    └─ 행동: 실행 계획에 따른 도구 순차 실행
    ↓
[F.LLM (Agent 2)]
    ├─ 추상 계획 → 구체적 실행 계획(JSON)
    └─ RAG로 계획 보강 (규칙 기반 폴백)
    ↓
[도구 실행]
    ├─ gemini_tryon: Gemini API 의류 분석·가상 피팅
    └─ function_product_search: 상품 검색 (Mock)
    ↓
[결과 검증 및 재시도 루프]
    ↓
[최종 결과] → 프론트엔드 (채팅·결과 뷰어·POC 안내)
```

---

## 📁 디렉토리 구조

### 전체 구조

```
Fashion-Agentic-AI-System/
├── .env.example              # 환경 변수 예시 (실제 .env는 Git 제외)
├── .gitignore
├── README.md                 # 현재 문서
│
├── agentic_system/            # 핵심 에이전트 시스템
│   ├── api/
│   │   └── main.py            # FastAPI 메인, /api/v1/request, 세션/파일 API
│   │
│   ├── core/
│   │   ├── agent_runtime.py   # Agent 1: 인식·판단·행동, 도구 등록/실행, 자기수정 루프
│   │   ├── f_llm.py           # Agent 2: 추상계획 → 실행계획(JSON), RAG 보강
│   │   ├── memory.py          # MemoryManager, ShortTermMemory (세션)
│   │   └── custom_ui.py       # 입력→Payload, 결과 포맷팅
│   │
│   ├── tools/
│   │   ├── gemini_tryon.py    # 가상 피팅 도구 (Gemini API)
│   │   └── functions.py       # 상품 검색 등 Function 도구
│   │
│   ├── data_stores/
│   │   ├── rag.py             # RAGStore: Mock + 로컬 + 외부 RAG 통합
│   │   ├── rag_local.py       # 로컬 문서 RAG (doc/, rag_fashion_1gb 등)
│   │   ├── rag_external.py    # 외부 웹 RAG (DuckDuckGo/Serper)
│   │   └── rag_vector.py      # Vector RAG (향후 확장)
│   │
│   ├── models/
│   │   └── internvl2_wrapper.py  # InternVL2-8B 래퍼 (선택 사용)
│   │
│   ├── data/
│   │   ├── local_rag_docs/    # 로컬 RAG 문서
│   │   └── rag_fashion_1gb/   # 패션 RAG 대용량 (수집 스크립트로 채움)
│   │
│   ├── scripts/
│   │   ├── collect_fashion_rag_data.py  # RAG 1GB 수집
│   │   ├── verify_rag_1gb.py             # RAG 1GB 검증
│   │   └── test_rag.py                   # RAG CLI 테스트
│   │
│   ├── frontend/              # React + Vite
│   │   ├── public/
│   │   │   └── system-diagram.jpg  # 종합 시스템 구성도
│   │   └── src/
│   │       ├── App.jsx
│   │       ├── main.jsx
│   │       ├── components/   # SimplePromptBar, ChatArea, ResultViewer, POCPillar 등
│   │       └── contexts/    # ThemeContext
│   │
│   └── requirements.txt
│
├── doc/                       # 문서
│   ├── 문서_분석_요약본.txt
│   ├── 코드_및_디렉토리_구조_가이드.md
│   └── RAG_테스트_안내.md
│
├── image/                     # 이미지 자산 (구성도 등)
├── model/                     # InternVL2-8B 등 (저장소 제외 가능)
├── uploads/                   # 사용자 업로드 (Git 제외)
├── outputs/                   # 생성 결과물 (Git 제외)
└── paper/                     # 논문·아키텍처 분석
```

### 핵심 파일 요약

| 경로 | 기능 |
|------|------|
| `agentic_system/api/main.py` | FastAPI 서버, 요청 → AgentRuntime → JSON 응답 |
| `agentic_system/core/agent_runtime.py` | Agent 1: 의도 분석, 추상계획, RAG, 실행계획, 도구 실행, 자기수정 루프 |
| `agentic_system/core/f_llm.py` | Agent 2: plan_type별 실행 steps(JSON) 생성, RAG 보강 |
| `agentic_system/core/memory.py` | 세션별 ShortTermMemory (대화 기록·컨텍스트) |
| `agentic_system/tools/gemini_tryon.py` | Gemini API 기반 의류 분석·가상 피팅 |
| `agentic_system/data_stores/rag.py` | 로컬+외부+Mock RAG 통합 |
| `agentic_system/frontend/src/App.jsx` | 프론트 상태·API 연동·채팅·결과 뷰 |

---

## 🛠️ 설치 방법

### 1. 전제 조건

- **Python 3.9+**
- **Node.js 18+ & npm** (프론트엔드용)
- **Git**

### 2. 저장소 클론

```bash
git clone https://github.com/heosanghun/Fashion-Agentic-AI-System_02.git
cd Fashion-Agentic-AI-System_02
```

### 3. Python 환경

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/macOS
# source venv/bin/activate

pip install -r agentic_system/requirements.txt
```

### 4. 환경 변수 (선택)

프로젝트 루트에 `.env` 파일 생성 (Git에 올리지 않음):

```ini
# 가상 피팅 (Gemini API)
GEMINI_API_KEY=your_gemini_api_key

# 대화 시 LLM 응답 (OpenAI, 선택)
OpenAI_API_Key=your_openai_api_key
```

### 5. 프론트엔드 (선택)

```bash
cd agentic_system/frontend
npm install
```

---

## 🚀 사용 방법

### 1. API 서버 실행

```bash
cd agentic_system
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

- **API 문서**: http://localhost:8000/docs  
- **헬스 체크**: http://localhost:8000/health  

### 2. 프론트엔드 실행

```bash
cd agentic_system/frontend
npm run dev
```

- **웹 UI**: http://localhost:5173  

### 3. RAG 테스트 (CLI)

```bash
python agentic_system/scripts/test_rag.py "오버사이즈란 뭐야?"
```

---

## 🏗️ 시스템 아키텍처 (요약)

```
[React Frontend]
       ↓
[FastAPI] → CustomUI → Agent Runtime (Agent 1)
       ↓                    ↓
       |              RAGStore (로컬+외부+Mock)
       |                    ↓
       |              F.LLM (Agent 2) → 실행 계획(JSON)
       |                    ↓
       |              도구 실행 (gemini_tryon, product_search)
       |                    ↓
       |              자기 수정 루프 → 결과 반환
       ↓
[채팅·결과 뷰·POC 안내]
```

---

## 🔧 환경 변수

| 변수명 | 설명 | 비고 |
|--------|------|------|
| `GEMINI_API_KEY` | Gemini API 키 | 가상 피팅 도구 사용 시 |
| `OpenAI_API_Key` / `OPENAI_API_KEY` | OpenAI API 키 | 대화 의도 시 LLM 응답 (선택) |

---

## 📄 문서

- **doc/문서_분석_요약본.txt**: 계획서·코드베이스 요약, 5대 패턴·데이터 플로우
- **doc/코드_및_디렉토리_구조_가이드.md**: 디렉토리·파일별 기능·작동 원리
- **doc/RAG_테스트_안내.md**: RAG 검증 방법

---

## 📞 문의

- **GitHub**: [heosanghun](https://github.com/heosanghun)
- **저장소**: [Fashion-Agentic-AI-System_02](https://github.com/heosanghun/Fashion-Agentic-AI-System_02)

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요! ⭐**

Made with ❤️ by heosanghun

</div>
