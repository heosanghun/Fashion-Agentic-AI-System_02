# Fashion Agentic AI System - 코드베이스 전체 분석

## 📋 목차

1. [프로젝트 구조 개요](#1-프로젝트-구조-개요)
2. [주요 디렉토리 분석](#2-주요-디렉토리-분석)
3. [핵심 모듈 상세 분석](#3-핵심-모듈-상세-분석)
4. [데이터 흐름 분석](#4-데이터-흐름-분석)
5. [파일 정리 가이드](#5-파일-정리-가이드)

---

## 1. 프로젝트 구조 개요

### 1.1 전체 디렉토리 트리

```
ChatGarment/
├── agentic_system/              # Agentic AI 메인 시스템
│   ├── api/                     # FastAPI 서버
│   ├── core/                    # 핵심 컴포넌트
│   ├── tools/                   # 도구 (Extensions & Functions)
│   ├── data_stores/             # RAG 데이터 저장소
│   ├── models/                  # AI 모델 래퍼
│   ├── frontend/                # React 프론트엔드
│   └── chatgarment_service/     # ChatGarment 마이크로서비스
│
├── ChatGarment/                 # ChatGarment 모델 (LLaVA 기반)
│   ├── llava/                   # LLaVA 모델 구현
│   ├── scripts/                 # 실행 스크립트
│   └── outputs/                 # 생성 결과
│
├── GarmentCodeRC/              # GarmentCode 라이브러리 (2D→3D 변환)
│   ├── pygarment/              # 핵심 라이브러리
│   ├── assets/                 # 자산 (패턴, 바디 모델 등)
│   └── gui/                    # GUI 인터페이스
│
├── chatgarment_service/        # 독립 ChatGarment 서비스
├── checkpoints/                # AI 모델 체크포인트
├── model/                      # InternVL2 모델
├── outputs/                    # 시스템 출력
├── uploads/                    # 사용자 업로드 파일
└── paper/                      # 논문 및 문서
```

### 1.2 파일 통계

- **Python 파일**: 약 590개
- **Markdown 문서**: 약 115개
- **JavaScript/JSX 파일**: 6개
- **JSON 설정 파일**: 33개
- **총 코드 라인 수**: 약 50,000+ 라인

---

## 2. 주요 디렉토리 분석

### 2.1 agentic_system/ - Agentic AI 메인 시스템

#### 2.1.1 api/ - FastAPI 서버

**파일**: `api/main.py`

**역할**: 
- REST API 엔드포인트 제공
- 사용자 요청 수신 및 이미지 저장
- Custom UI 및 Agent Runtime 호출

**주요 엔드포인트**:
- `POST /api/v1/request`: 메인 요청 처리
- `POST /api/v1/request/json`: JSON 형식 요청
- `GET /api/v1/session/{session_id}/history`: 세션 기록 조회
- `DELETE /api/v1/session/{session_id}`: 세션 삭제
- `GET /api/v1/file`: 파일 제공

**핵심 코드 구조**:
```python
# 전역 컴포넌트 초기화
memory_manager = MemoryManager()
rag_store = RAGStore()
agent2 = FLLM(model_name="internvl2-8b", ...)
agent_runtime = AgentRuntime(agent2=agent2, memory_manager=memory_manager)

# 도구 등록
agent_runtime.register_tool("extensions_2d_to_3d", extensions_2d_to_3d_tool)
agent_runtime.register_tool("function_product_search", product_search_function_tool)
```

#### 2.1.2 core/ - 핵심 컴포넌트

**주요 파일**:

1. **agent_runtime.py** (Agent 1)
   - 역할: 종합 감독 에이전트
   - 주요 메서드:
     - `process_request()`: 요청 처리 메인 함수
     - `_analyze_user_intent()`: 사용자 의도 분석
     - `_create_abstract_plan()`: 추상적 계획 수립
     - `_execute_plan()`: 실행 계획 실행
     - `_self_correction_loop()`: 자기 수정 루프

2. **f_llm.py** (Agent 2)
   - 역할: 작업 지시 전문가 에이전트
   - 주요 메서드:
     - `generate_execution_plan()`: 구체적 실행 계획 생성
     - `_create_execution_steps()`: 실행 단계 생성
     - `_generate_plan_with_llm()`: LLM 기반 계획 생성 (선택적)

3. **custom_ui.py**
   - 역할: 사용자 입력 처리 및 결과 포맷팅
   - 주요 메서드:
     - `process_user_input()`: 입력 데이터 구조화
     - `format_output()`: 결과 포맷팅

4. **memory.py**
   - 역할: 세션 메모리 관리
   - 주요 클래스:
     - `ShortTermMemory`: 세션 기반 단기 메모리
     - `LongTermMemory`: 사용자 기반 장기 메모리 (향후 구현)
     - `MemoryManager`: 메모리 관리자

#### 2.1.3 tools/ - 도구 시스템

**주요 파일**:

1. **extensions.py** (Extensions Tool)
   - 역할: 2D→3D 변환 도구
   - 주요 클래스: `Extensions2DTo3D`
   - 주요 메서드:
     - `execute()`: 도구 실행 메인 함수
     - `_analyze_image()`: 이미지 분석
     - `_generate_pattern()`: 패턴 생성
     - `_convert_to_3d()`: 3D 변환
     - `_render_result()`: 렌더링

2. **chatgarment_integration.py**
   - 역할: ChatGarment 파이프라인 통합
   - 주요 클래스: `ChatGarmentPipeline`
   - 주요 메서드:
     - `load_model()`: 모델 로딩
     - `analyze_image()`: 이미지 분석
     - `process_image_to_garment()`: 전체 파이프라인 실행

3. **functions.py** (Functions Tool)
   - 역할: 상품 검색 도구
   - 주요 클래스: `ProductSearchFunction`
   - PoC 단계에서는 Mock 데이터 사용

4. **extensions_service.py**
   - 역할: ChatGarment 마이크로서비스 통합
   - HTTP API를 통한 서비스 호출

#### 2.1.4 data_stores/ - RAG 데이터 저장소

**주요 파일**:

1. **rag.py**
   - 역할: Mock RAG 구현
   - 주요 클래스:
     - `MockRAG`: 규칙 기반 지식 검색
     - `RAGStore`: RAG 스토어 래퍼

2. **rag_vector.py** (향후 구현)
   - 역할: Vector DB 기반 RAG
   - ChromaDB/FAISS 통합 예정

#### 2.1.5 models/ - AI 모델 래퍼

**주요 파일**:

1. **internvl2_wrapper.py**
   - 역할: InternVL2-8B 모델 래퍼
   - 주요 메서드:
     - `load_model()`: 모델 로딩
     - `chat()`: 대화 형식 추론
     - `generate_text()`: 텍스트 생성
     - `analyze_image()`: 이미지 분석

#### 2.1.6 frontend/ - React 프론트엔드

**주요 파일**:

1. **src/App.jsx**
   - 역할: 메인 애플리케이션 컴포넌트
   - 상태 관리 및 API 호출

2. **src/components/ImageUpload.jsx**
   - 역할: 이미지 업로드 컴포넌트

3. **src/components/StatusBar.jsx**
   - 역할: 상태 표시 컴포넌트

4. **src/components/ResultViewer.jsx**
   - 역할: 결과 표시 컴포넌트

5. **src/components/ModelViewer.jsx**
   - 역할: 3D 모델 뷰어 (Three.js)

### 2.2 ChatGarment/ - LLaVA 기반 의류 생성 모델

#### 2.2.1 llava/ - LLaVA 모델 구현

**주요 파일**:

1. **garment_utils_v2.py**
   - 역할: 의류 생성 유틸리티
   - 주요 함수:
     - `try_generate_garments()`: 의류 생성 시도
     - `run_garmentcode_parser_float50()`: GarmentCode 파서 실행

2. **garmentcode_utils.py**
   - 역할: GarmentCode 통합

3. **garmentcodeRC_utils.py**
   - 역할: GarmentCodeRC 통합

4. **json_fixer.py**
   - 역할: JSON 출력 수정 및 검증

5. **model/** - 모델 아키텍처
   - `llava_arch.py`: LLaVA 아키텍처 정의
   - `language_model/`: 언어 모델 구현

#### 2.2.2 scripts/ - 실행 스크립트

- 이미지 기반 생성 스크립트
- 텍스트 기반 생성 스크립트
- 편집 기능 스크립트

### 2.3 GarmentCodeRC/ - 2D→3D 변환 라이브러리

#### 2.3.1 pygarment/ - 핵심 라이브러리

**주요 모듈**:

1. **garmentcode/**: 패턴 생성 엔진
2. **meshgen/**: 3D 메시 생성
3. **pattern/**: 패턴 렌더링

### 2.4 기타 디렉토리

- **checkpoints/**: AI 모델 체크포인트 (Git 제외)
- **model/**: InternVL2 모델 파일 (Git 제외)
- **outputs/**: 시스템 출력 파일 (Git 제외)
- **uploads/**: 사용자 업로드 파일 (Git 제외)

---

## 3. 핵심 모듈 상세 분석

### 3.1 Agent Runtime (Agent 1)

**파일**: `agentic_system/core/agent_runtime.py`

**클래스**: `AgentRuntime`

**주요 흐름**:

```python
def process_request(self, payload, session_id):
    # 1. 인식 (Perception)
    user_intent = self._analyze_user_intent(payload)
    
    # 2. 판단 (Judgment)
    abstract_plan = self._create_abstract_plan(user_intent, payload, memory)
    execution_plan = self.agent2.generate_execution_plan(...)
    
    # 3. 행동 (Action)
    execution_result = self._execute_plan(execution_plan, memory)
    
    # 4. 자기 수정 루프
    final_result = self._self_correction_loop(...)
    
    return final_result
```

**의존성**:
- `FLLM` (Agent 2)
- `MemoryManager`
- `tools_registry` (등록된 도구들)

### 3.2 F.LLM (Agent 2)

**파일**: `agentic_system/core/f_llm.py`

**클래스**: `FLLM`

**주요 흐름**:

```python
def generate_execution_plan(self, abstract_plan, context, ...):
    # LLM 기반 계획 생성 (선택적)
    if use_llm:
        enhanced_plan = self._generate_plan_with_llm(...)
    else:
        enhanced_plan = abstract_plan  # 규칙 기반
    
    # 실행 단계 생성
    steps = self._create_execution_steps(enhanced_plan, context)
    
    return ExecutionPlan(steps=steps, ...)
```

**의존성**:
- `InternVL2Wrapper` (선택적)
- `RAGStore` (선택적)

### 3.3 Extensions Tool

**파일**: `agentic_system/tools/extensions.py`

**클래스**: `Extensions2DTo3D`

**주요 흐름**:

```python
def execute(self, action, parameters, context):
    if action == "analyze_image":
        return self._analyze_image(parameters, context)
    elif action == "generate_pattern":
        return self._generate_pattern(parameters, context)
    elif action == "convert_to_3d":
        return self._convert_to_3d(parameters, context)
    elif action == "render_result":
        return self._render_result(parameters, context)
```

**의존성**:
- `ChatGarmentPipeline`
- `GarmentCodeRC` (간접적)

### 3.4 ChatGarment Pipeline

**파일**: `agentic_system/tools/chatgarment_integration.py`

**클래스**: `ChatGarmentPipeline`

**주요 흐름**:

```python
def process_image_to_garment(self, image_path, ...):
    # 1. 이미지 로딩 및 전처리
    image = Image.open(image_path).convert('RGB')
    
    # 2. Step 1: Geometry features 추출
    json_output1 = self._extract_geometry_features(image)
    
    # 3. Step 2: Sewing pattern code 생성
    json_output2, float_preds = self._generate_pattern_code(image, json_output1)
    
    # 4. GarmentCode 패턴 생성
    pattern_path = run_garmentcode_parser_float50(...)
    
    # 5. 3D 변환
    mesh_path = self._convert_to_3d(pattern_path, ...)
    
    return result
```

---

## 4. 데이터 흐름 분석

### 4.1 전체 데이터 흐름

```
사용자 입력 (텍스트 + 이미지)
    ↓
[Frontend] FormData 생성
    ↓ HTTP POST
[API Server] 이미지 저장, Custom UI 호출
    ↓ JSONPayload
[Agent Runtime] 의도 분석, 추상적 계획 수립
    ↓ AbstractPlan
[F.LLM] 구체적 실행 계획 생성
    ↓ ExecutionPlan
[Agent Runtime] 도구 실행 오케스트레이션
    ↓
[Extensions Tool] ChatGarment Pipeline 호출
    ↓
[ChatGarment] 이미지 분석 → 패턴 생성
    ↓ JSON + Float Predictions
[GarmentCodeRC] 3D 메시 생성
    ↓ OBJ 파일
[Extensions Tool] 렌더링
    ↓
[API Server] 결과 반환
    ↓ JSON Response
[Frontend] 결과 시각화
```

### 4.2 주요 데이터 구조

#### 4.2.1 JSONPayload

```python
{
    "timestamp": "2025-01-01T12:00:00",
    "user_id": "user123",
    "session_id": "session456",
    "input_data": {
        "text": "이 옷을 입혀줘",
        "image_path": "/path/to/image.jpg",
        "has_image": true
    },
    "metadata": {
        "input_type": "text_and_image",
        "processed_at": "2025-01-01T12:00:00"
    }
}
```

#### 4.2.2 ExecutionPlan

```python
{
    "plan_id": "plan_20250101120000",
    "steps": [
        {
            "step_id": 1,
            "tool": "extensions_2d_to_3d",
            "action": "analyze_image",
            "parameters": {...},
            "dependencies": []
        },
        ...
    ],
    "tools_required": ["extensions_2d_to_3d"],
    "estimated_time": 30.0
}
```

#### 4.2.3 ChatGarment 출력

```python
{
    "status": "success",
    "analysis": {
        "upper_garment": ["T-shirt", "short sleeves"],
        "lower_garment": []
    },
    "text_output": "...",
    "float_preds": [...],
    "json_spec_path": "/path/to/specification.json",
    "mesh_path": "/path/to/mesh.obj"
}
```

---

## 5. 파일 정리 가이드

### 5.1 필수 파일 (핵심 기능)

#### agentic_system/
- `api/main.py` - API 서버
- `core/agent_runtime.py` - Agent 1
- `core/f_llm.py` - Agent 2
- `core/custom_ui.py` - UI 컴포넌트
- `core/memory.py` - 메모리 관리
- `tools/extensions.py` - 2D→3D 도구
- `tools/chatgarment_integration.py` - ChatGarment 통합
- `tools/functions.py` - 상품 검색 도구
- `data_stores/rag.py` - RAG 스토어
- `models/internvl2_wrapper.py` - InternVL2 래퍼

#### frontend/
- `src/App.jsx` - 메인 앱
- `src/components/*.jsx` - 모든 컴포넌트
- `package.json` - 의존성
- `vite.config.js` - 빌드 설정

### 5.2 문서 파일

#### 루트 디렉토리
- `README.md` - 프로젝트 개요
- `PROJECT_STRUCTURE_ANALYSIS.md` - 구조 분석
- `CODE_REVIEW_REPORT.md` - 코드 검토

#### agentic_system/
- `README.md` - 시스템 문서
- `ARCHITECTURE.md` - 아키텍처 문서
- `IMPLEMENTATION_STATUS.md` - 구현 상태

#### paper/
- `Fashion_Agentic_AI_System_Paper.md` - 논문
- `CODEBASE_ANALYSIS.md` - 코드베이스 분석 (본 문서)

### 5.3 설정 파일

- `requirements.txt` - Python 의존성
- `package.json` - Node.js 의존성
- `.gitignore` - Git 제외 파일
- `pyproject.toml` - Python 프로젝트 설정 (ChatGarment, GarmentCodeRC)

### 5.4 제외할 파일 (Git 제외)

- `checkpoints/` - 모델 체크포인트 (용량 큼)
- `model/InternVL2_8B/*.safetensors` - 모델 가중치
- `outputs/` - 생성된 결과 파일
- `uploads/` - 사용자 업로드 파일
- `__pycache__/` - Python 캐시
- `node_modules/` - Node.js 패키지
- `*.log` - 로그 파일

### 5.5 정리 권장사항

1. **테스트 파일 정리**
   - `test_*.py` 파일들을 `tests/` 디렉토리로 이동
   - 통합 테스트와 단위 테스트 분리

2. **문서 파일 정리**
   - 모든 `.md` 파일을 `docs/` 디렉토리로 이동
   - 논문 관련 파일은 `paper/` 디렉토리 유지

3. **스크립트 파일 정리**
   - 실행 스크립트를 `scripts/` 디렉토리로 이동
   - 설정 스크립트와 실행 스크립트 분리

4. **임시 파일 삭제**
   - `*.txt` (로그 파일 등)
   - `*.json` (테스트 결과 파일 등)
   - 중복된 문서 파일

---

## 6. 코드베이스 통계

### 6.1 언어별 코드 분포

- **Python**: 약 85% (핵심 로직)
- **JavaScript/JSX**: 약 10% (프론트엔드)
- **Markdown**: 약 5% (문서)

### 6.2 모듈별 코드 라인 수

- `agentic_system/core/`: 약 1,500 라인
- `agentic_system/tools/`: 약 2,000 라인
- `agentic_system/api/`: 약 300 라인
- `ChatGarment/llava/`: 약 10,000+ 라인
- `GarmentCodeRC/pygarment/`: 약 5,000+ 라인
- `frontend/src/`: 약 500 라인

### 6.3 의존성 분석

**주요 Python 패키지**:
- `torch>=2.1.2` - PyTorch
- `transformers>=4.37.2` - Hugging Face
- `fastapi>=0.100.0` - FastAPI
- `pillow` - 이미지 처리
- `numpy` - 수치 연산

**주요 JavaScript 패키지**:
- `react>=18.2.0` - React
- `three>=0.158.0` - Three.js
- `axios>=1.6.0` - HTTP 클라이언트
- `vite>=5.0.0` - 빌드 도구

---

## 7. 결론

본 코드베이스는 Agentic AI 프레임워크를 기반으로 한 복잡한 의류 생성 시스템을 구현하고 있다. 멀티 에이전트 아키텍처와 도구 시스템을 통해 확장 가능하고 유지보수가 용이한 구조를 제공한다.

주요 특징:
- **모듈화된 구조**: 각 컴포넌트가 독립적으로 작동
- **확장 가능성**: 새로운 도구를 쉽게 추가 가능
- **문서화**: 상세한 문서와 주석 제공
- **테스트 가능성**: 각 모듈이 독립적으로 테스트 가능

