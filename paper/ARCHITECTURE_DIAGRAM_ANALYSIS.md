# Agentic System & ChatGarment Integration Workflow - 아키텍처 다이어그램 상세 분석

## 📋 목차

1. [다이어그램 개요](#1-다이어그램-개요)
2. [각 컴포넌트 상세 분석](#2-각-컴포넌트-상세-분석)
3. [데이터 흐름 분석](#3-데이터-흐름-분석)
4. [통합 포인트 분석](#4-통합-포인트-분석)
5. [실행 시퀀스 상세](#5-실행-시퀀스-상세)

---

## 1. 다이어그램 개요

본 다이어그램은 **"Agentic System & ChatGarment Integration Workflow"**를 시각화한 것으로, 사용자 입력부터 3D 의류 모델 생성까지의 전체 워크플로우를 보여줍니다.

### 1.1 전체 구조

```
[사용자] → [Frontend] → [API Server] → [Agentic System] → [ChatGarment Ecosystem] → [결과 반환]
```

### 1.2 주요 계층

1. **사용자 인터페이스 계층**: User, Frontend
2. **API 게이트웨이 계층**: API Server
3. **Agentic AI 계층**: Agent Runtime (Agent 1), F.LLM (Agent 2)
4. **도구 계층**: Extension Tool
5. **AI 모델 계층**: ChatGarment 모델, GarmentCodeRC
6. **결과 계층**: 최종 결과 반환

---

## 2. 각 컴포넌트 상세 분석

### 2.1 사용자 (User) - 입력 계층

**위치**: 다이어그램 최상단 왼쪽

**역할**: 시스템의 시작점

**입력 형식**:
- **텍스트 입력**: 자연어 요청 (예: "이 옷을 입혀줘", "3D로 만들어줘")
- **이미지 입력**: 의류 이미지 파일 (JPG, PNG 등)

**특징**:
- 멀티모달 입력 지원 (텍스트 + 이미지 동시 입력 가능)
- 사용자는 텍스트만, 이미지만, 또는 둘 다 입력 가능

**데이터 형식**:
```
{
  "text": "이 옷을 입혀줘",
  "image": <이미지 파일 바이너리>
}
```

---

### 2.2 Frontend (React + Vite) - 프레젠테이션 계층

**위치**: 사용자 오른쪽

**포트**: 5173

**기술 스택**:
- React 18.2.0
- Vite 5.0.0 (빌드 도구)
- Three.js (3D 뷰어)

**주요 기능**:

#### 2.2.1 파일 업로드 (File Upload)
- 드래그 앤 드롭 지원
- 파일 선택 다이얼로그
- 이미지 미리보기
- 파일 형식 검증 (PNG, JPG, JPEG)

#### 2.2.2 텍스트 입력 (Text Input)
- 텍스트 입력 필드
- 자동 완성 (향후 구현)
- 입력 검증

#### 2.2.3 결과 시각화 (Result Visualization)
- 3D 모델 뷰어 (Three.js)
- 분석 결과 표시
- 패턴 정보 표시
- 렌더링 이미지 갤러리

**연결**:
- **출력**: `HTTP POST /api/v1/request` → API Server
- **입력**: JSON Response ← API Server

**데이터 전송 형식**:
```javascript
const formData = new FormData();
formData.append('text', textInput);
formData.append('image', imageFile);
formData.append('session_id', sessionId);

axios.post('http://localhost:8000/api/v1/request', formData);
```

---

### 2.3 API Server (FastAPI) - API 게이트웨이 계층

**위치**: 다이어그램 상단 오른쪽

**포트**: 8000

**기술 스택**:
- FastAPI 0.100+
- Uvicorn (ASGI 서버)
- CORS 미들웨어

**주요 기능**:

#### 2.3.1 요청 수신 및 이미지 저장
```python
@app.post("/api/v1/request")
async def process_request(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None)
):
    # 이미지 저장
    upload_dir = project_root / "uploads"
    image_path = upload_dir / f"{session_id}_{image.filename}"
    with open(image_path, "wb") as f:
        f.write(await image.read())
```

**저장 위치**: `uploads/{session_id}_{filename}`

#### 2.3.2 Custom UI 호출
- 사용자 입력을 JSON Payload로 구조화
- 세션 ID 생성 (없는 경우)
- 입력 검증

#### 2.3.3 Agent Runtime 호출
- 구조화된 Payload를 Agent Runtime에 전달
- 결과 수신 및 포맷팅

**연결**:
- **입력**: `HTTP POST /api/v1/request` ← Frontend
- **출력**: `JSONPayload` → Agent Runtime (Agent 1)
- **입력**: `Final Result` ← Agent Runtime
- **출력**: `JSONResponse` → Frontend

---

### 2.4 Agentic System - 지능형 오케스트레이션 계층

**위치**: 다이어그램 중앙 (큰 파란색 박스)

**역할**: 전체 프로세스의 두뇌 역할

#### 2.4.1 Agent Runtime (Agent 1) - 종합 감독

**파일**: `core/agent_runtime.py`

**역할**: 종합 감독 에이전트 (Overall Supervisor)

**3단계 프로세스**:

##### 1️⃣ 인식 (Perception)

**기능**: 사용자 의도 분석 및 작업 유형 판단

**처리 내용**:
- 텍스트 키워드 분석
- 이미지 존재 여부 확인
- 의도 유형 분류:
  - **3D 생성 (3d_generation)**: "입혀줘", "가상 피팅" 등의 키워드 또는 이미지 입력
  - **상품 추천 (garment_recommendation)**: "추천", "찾아줘" 등의 키워드

**출력**:
```python
{
    "type": "3d_generation",
    "confidence": 0.9,
    "text": "이 옷을 입혀줘",
    "has_image": True
}
```

##### 2️⃣ 판단 (Judgment)

**기능**: 추상적 작업 계획 수립 및 Agent 2에게 전달

**처리 내용**:
- 사용자 의도를 기반으로 추상적 계획 생성
- 계획 유형 결정 (3D 생성 vs 상품 추천)
- Agent 2에게 계획 전달

**출력 (AbstractPlan)**:
```python
{
    "plan_type": "3d_generation",
    "goal": "2D 이미지를 3D 가상 피팅으로 변환",
    "steps": [
        "의류 이미지 분석",
        "3D 패턴 생성",
        "3D 모델 변환",
        "렌더링 및 시각화"
    ],
    "parameters": {
        "image_path": "/path/to/image.jpg",
        "text": "이 옷을 입혀줘"
    }
}
```

**연결**: `generate_execution_plan()` → F.LLM (Agent 2)

##### 3️⃣ 행동 (Action)

**기능**: 실행 계획의 각 단계를 순차적으로 실행

**처리 내용**:
- Agent 2로부터 받은 실행 계획 파싱
- 각 단계를 순차적으로 실행
- 등록된 도구 호출 (`tools_registry`)
- 의존성 관리 (이전 단계 결과를 다음 단계로 전달)

**의존성 관리 예시**:
```python
# Step 1 실행
step1_result = tool_func("analyze_image", params1, context)

# Step 2 실행 (Step 1 결과 필요)
params2["_dependency_result"] = step1_result
step2_result = tool_func("generate_pattern", params2, context)

# Step 3 실행 (Step 2 결과 필요)
params3["_dependency_result"] = step2_result
step3_result = tool_func("convert_to_3d", params3, context)
```

**연결**: `tools_registry['extensions_2d_to_3d']()` → Extension Tool

---

#### 2.4.2 F.LLM (Agent 2) - 작업 지시 전문가

**파일**: `core/f_llm.py`

**역할**: 작업 지시 전문가 (Task Instruction Expert)

**모델**: InternVL2-8B (선택적 사용)

**주요 기능**:

##### 추상적 계획 → 구체적 실행 계획 변환

**입력**: AbstractPlan (Agent 1로부터)

**처리**:
1. 추상적 계획 분석
2. 구체적 실행 단계 생성
3. JSON 형식으로 구조화

**출력 (ExecutionPlan)**:
```json
{
  "plan_id": "plan_20250101120000",
  "steps": [
    {
      "step_id": 1,
      "tool": "extensions_2d_to_3d",
      "action": "analyze_image",
      "parameters": {
        "image_path": "/path/to/image.jpg",
        "text_description": "이 옷을 입혀줘"
      },
      "dependencies": []
    },
    {
      "step_id": 2,
      "tool": "extensions_2d_to_3d",
      "action": "generate_pattern",
      "parameters": {},
      "dependencies": [1]
    },
    {
      "step_id": 3,
      "tool": "extensions_2d_to_3d",
      "action": "convert_to_3d",
      "parameters": {},
      "dependencies": [2]
    },
    {
      "step_id": 4,
      "tool": "extensions_2d_to_3d",
      "action": "render_result",
      "parameters": {},
      "dependencies": [3]
    }
  ],
  "tools_required": ["extensions_2d_to_3d"],
  "estimated_time": 30.0
}
```

**연결**:
- **입력**: `generate_execution_plan()` ← Agent Runtime (Agent 1)
- **출력**: `ExecutionPlan (JSON Steps)` → Agent Runtime (Agent 1)

**특징**:
- 현재 PoC 단계에서는 규칙 기반 모드가 기본값
- 향후 Pilot 단계에서 InternVL2 모델을 사용한 LLM 기반 계획 생성 활성화 예정

---

### 2.5 Extension Tool - 도구 계층

**위치**: Agent Runtime (Agent 1) 아래

**파일**: `tools/extensions.py`

**클래스**: `Extensions2DTo3D`

**역할**: ChatGarment 통합 도구

**주요 기능**:
- 2D 이미지를 3D 모델로 변환하는 모든 단계 처리
- ChatGarment Pipeline과 GarmentCodeRC를 통합

**연결**:
- **입력**: `tools_registry['extensions_2d_to_3d']()` ← Agent Runtime (Agent 1)
- **출력**: Integration Switch로 분기

**지원하는 액션**:
1. `analyze_image`: 이미지 분석
2. `generate_pattern`: 패턴 생성
3. `convert_to_3d`: 3D 변환
4. `render_result`: 렌더링

---

### 2.6 Integration Switch - 통합 스위치

**위치**: Extension Tool 오른쪽 (회색 박스)

**역할**: ChatGarment 통합 방식 선택

**두 가지 경로**:

#### 2.6.1 직접 사용 (Local Integration)

**경로**: Extension Tool → ChatGarment 모델 (직접 통합)

**특징**:
- 같은 프로세스에서 ChatGarment Pipeline 직접 호출
- 빠른 응답 속도
- 단일 프로세스에서 모든 모델 로드

**사용 시나리오**:
- 개발 환경
- 단일 서버 배포
- 빠른 프로토타이핑

**코드 예시**:
```python
# extensions.py
if self.chatgarment_pipeline:
    result = self.chatgarment_pipeline.analyze_image(image_path)
```

#### 2.6.2 마이크로서비스 (Microservice)

**경로**: Extension Tool → ChatGarment Service (독립 서버)

**포트**: 9000

**특징**:
- 독립적인 서비스로 분리
- HTTP API를 통한 통신
- 독립적 스케일링 가능
- GPU 서버 분산 배치 가능

**사용 시나리오**:
- 프로덕션 환경
- 대규모 배포
- 리소스 분리 필요 시

**코드 예시**:
```python
# extensions_service.py
response = requests.post(
    "http://localhost:9000/api/v1/process",
    files={"image": open(image_path, "rb")}
)
```

**환경 변수 제어**:
```python
USE_CHATGARMENT_SERVICE = os.getenv("USE_CHATGARMENT_SERVICE", "false")
CHATGARMENT_SERVICE_URL = os.getenv("CHATGARMENT_SERVICE_URL", "http://localhost:9000")
```

---

### 2.7 ChatGarment Ecosystem - AI 모델 계층

**위치**: 다이어그램 하단 (큰 주황색 박스)

**역할**: 의류 생성의 핵심 능력

#### 2.7.1 ChatGarment 모델 (LLaVA 기반)

**파일**: `tools/chatgarment_integration.py`

**모델**: LLaVA-1.5-7B + ChatGarment 파인튜닝

**주요 프로세스**:

##### 단계 1: 이미지 분석 (Geometry Features)

**입력**: 이미지 파일

**처리**:
1. 이미지 전처리 (리사이즈, 패딩)
2. Vision Encoder를 통한 이미지 임베딩
3. Language Model을 통한 텍스트 생성
4. JSON 형식으로 구조화

**프롬프트**:
```
"Can you describe the geometry features of the garments 
worn by the model in the Json format?"
```

**출력**:
```json
{
  "upper_garment": ["T-shirt", "short sleeves", "crew neck"],
  "lower_garment": []
}
```

또는

```json
{
  "wholebody_garment": ["dress", "long length", "sleeveless"]
}
```

##### 단계 2: 패턴 코드 생성 (Sewing Pattern Code)

**입력**: 
- Step 1의 Geometry Features 결과
- 원본 이미지

**처리**:
1. Step 1 결과를 컨텍스트로 사용
2. 재봉 패턴 코드 생성
3. Float 예측값 생성 (GarmentCode 파라미터)

**프롬프트**:
```
"Can you estimate the sewing pattern code based on the 
image and Json format garment geometry description?"
```

**출력**:
```json
{
  "upperbody_garment": {
    "front": {
      "width": 50.0,
      "height": 70.0,
      "seams": ["shoulder", "side", "bottom"]
    },
    "back": {...},
    "sleeves": {...}
  }
}
```

**Float Predictions**: `[0.5, 0.3, 0.8, ...]` (50개의 float 값)

**연결**: → GarmentCodeRC (2D→3D 변환)

---

#### 2.7.2 GarmentCodeRC (2D→3D 변환)

**파일**: `ChatGarment/llava/garment_utils_v2.py`

**역할**: 2D 패턴을 3D 메시로 변환

**주요 기능**:

##### 패턴 JSON 생성

**입력**: ChatGarment의 JSON 출력 + Float Predictions

**처리**:
- `run_garmentcode_parser_float50()` 함수 호출
- GarmentCode 사양 형식으로 변환
- 패널(panel), 엣지(edge), 시임(seam) 정보 생성

**출력**: `specification.json` 파일

**파일 구조**:
```json
{
  "garment_type": "TShirt",
  "components": ["front", "back", "sleeves"],
  "specification": {
    "front": {
      "width": 50.0,
      "height": 70.0,
      "vertices": [[x1, y1], [x2, y2], ...],
      "edges": [[v1, v2], [v2, v3], ...],
      "seams": ["shoulder", "side", "bottom"]
    },
    ...
  }
}
```

##### 물리 시뮬레이션

**입력**: 패턴 JSON 파일

**처리**:
- GarmentCodeRC 시뮬레이터 실행
- 의류 드레이핑 시뮬레이션
- 중력, 마찰, 탄성 등의 물리 속성 적용

**스크립트**: `ChatGarment/run_garmentcode_sim.py`

**명령어**:
```bash
python run_garmentcode_sim.py --json_spec_file pattern.json
```

##### 3D 메시 생성 (.obj 파일)

**출력**: `garment_sim.obj` 파일

**파일 형식**:
```
# OBJ 파일 형식
v -1.0 -1.0 -1.0    # 정점 (vertex)
v 1.0 -1.0 -1.0
v 1.0 1.0 -1.0
...
f 1 2 3 4           # 면 (face)
f 5 6 7 8
...
```

**연결**: → 결과 반환 (Final Result)

---

### 2.8 결과 반환 (Final Result) - 출력 계층

**위치**: 다이어그램 최우측

**역할**: 최종 결과 구조화 및 반환

**출력 구조**:
```json
{
  "status": "success",
  "analysis": {
    "upper_garment": ["T-shirt", "short sleeves"],
    "lower_garment": []
  },
  "pattern_path": "/path/to/specification.json",
  "mesh_path": "/path/to/garment_sim.obj",
  "render_path": "/path/to/garment_render.png",
  "message": "의류 생성이 성공적으로 완료되었습니다!"
}
```

**필드 설명**:

- **status**: 작업 상태 ("success", "error", "processing")
- **analysis**: 이미지 분석 결과 (ChatGarment Step 1 출력)
- **pattern_path**: 생성된 패턴 JSON 파일 경로
- **mesh_path**: 생성된 3D 메시 파일 경로 (.obj)
- **render_path**: 렌더링된 이미지 파일 경로 (.png)

**연결**: → API Server → Frontend → 사용자

---

## 3. 데이터 흐름 분석

### 3.1 전체 데이터 흐름

```
[1] 사용자 입력
    ├─ 텍스트: "이 옷을 입혀줘"
    └─ 이미지: TShirt.jpg
        ↓
[2] Frontend (React + Vite)
    ├─ FormData 생성
    ├─ session_id 생성
    └─ HTTP POST 요청
        ↓
[3] API Server (FastAPI)
    ├─ 이미지 저장: uploads/session_12345_TShirt.jpg
    ├─ Custom UI 호출 → JSONPayload 생성
    └─ Agent Runtime 호출
        ↓
[4] Agent Runtime (Agent 1)
    ├─ [인식] 사용자 의도 분석
    │   └─ {"type": "3d_generation", "confidence": 0.9}
    ├─ [판단] 추상적 계획 수립
    │   └─ AbstractPlan 생성
    └─ Agent 2 호출
        ↓
[5] F.LLM (Agent 2)
    ├─ 추상적 계획 → 구체적 실행 계획 변환
    └─ ExecutionPlan (JSON Steps) 반환
        ↓
[6] Agent Runtime (Agent 1)
    ├─ [행동] 실행 계획 실행
    └─ Extension Tool 호출
        ↓
[7] Extension Tool
    ├─ Integration Switch 선택
    └─ ChatGarment 통합
        ↓
[8] ChatGarment 모델
    ├─ Step 1: 이미지 분석 (Geometry Features)
    │   └─ JSON: {"upper_garment": [...]}
    └─ Step 2: 패턴 코드 생성 (Sewing Pattern Code)
        └─ JSON + Float Predictions
        ↓
[9] GarmentCodeRC
    ├─ 패턴 JSON 생성
    ├─ 물리 시뮬레이션
    └─ 3D 메시 생성 (.obj)
        ↓
[10] 결과 반환
    ├─ JSON 구조화
    └─ API Server로 반환
        ↓
[11] Frontend
    ├─ 결과 수신
    └─ 3D 뷰어에 표시
```

### 3.2 단계별 데이터 변환

#### Step 1: 이미지 분석

**입력**: 이미지 파일 (JPG/PNG)
**처리**: ChatGarment 모델 (LLaVA)
**출력**: 
```json
{
  "analysis": {
    "upper_garment": ["T-shirt", "short sleeves"],
    "lower_garment": []
  },
  "text_output": "...",
  "float_preds": [0.5, 0.3, 0.8, ...]
}
```

#### Step 2: 패턴 생성

**입력**: Step 1의 JSON + Float Predictions
**처리**: GarmentCode 파서
**출력**: 
```json
{
  "pattern_path": "/path/to/specification.json",
  "pattern_info": {
    "type": "TShirt",
    "components": ["front", "back", "sleeves"]
  }
}
```

#### Step 3: 3D 변환

**입력**: 패턴 JSON 파일
**처리**: GarmentCodeRC 시뮬레이션
**출력**: 
```json
{
  "mesh_path": "/path/to/garment_sim.obj",
  "mesh_info": {
    "vertices": 1000,
    "faces": 2000,
    "format": "obj"
  }
}
```

#### Step 4: 렌더링

**입력**: 3D 메시 파일
**처리**: 렌더링 엔진
**출력**: 
```json
{
  "render_path": "/path/to/garment_render.png",
  "visualization": {
    "image_path": "/path/to/garment_render.png",
    "mesh_path": "/path/to/garment_sim.obj"
  }
}
```

---

## 4. 통합 포인트 분석

### 4.1 Frontend ↔ API Server

**프로토콜**: HTTP/HTTPS
**메서드**: POST
**엔드포인트**: `/api/v1/request`
**데이터 형식**: `multipart/form-data`

**요청 구조**:
```
Content-Type: multipart/form-data

text: "이 옷을 입혀줘"
image: <이미지 파일 바이너리>
session_id: "session_12345"
```

**응답 구조**:
```json
{
  "status": "success",
  "message": "의류 생성이 완료되었습니다.",
  "data": {
    "analysis": {...},
    "pattern_path": "...",
    "mesh_path": "...",
    "render_path": "..."
  }
}
```

### 4.2 API Server ↔ Agent Runtime

**프로토콜**: Python 함수 호출
**데이터 형식**: JSONPayload (Pydantic 모델)

**요청 구조**:
```python
{
    "timestamp": "2025-01-01T12:00:00",
    "user_id": "user123",
    "session_id": "session456",
    "input_data": {
        "text": "이 옷을 입혀줘",
        "image_path": "/path/to/image.jpg",
        "has_image": True
    },
    "metadata": {...}
}
```

### 4.3 Agent Runtime ↔ F.LLM

**프로토콜**: Python 함수 호출
**메서드**: `generate_execution_plan()`

**요청 구조**:
```python
{
    "plan_type": "3d_generation",
    "goal": "2D 이미지를 3D 가상 피팅으로 변환",
    "steps": ["의류 이미지 분석", "3D 패턴 생성", ...],
    "parameters": {
        "image_path": "/path/to/image.jpg",
        "text": "이 옷을 입혀줘"
    }
}
```

**응답 구조**: ExecutionPlan (JSON Steps)

### 4.4 Agent Runtime ↔ Extension Tool

**프로토콜**: Python 함수 호출
**레지스트리**: `tools_registry['extensions_2d_to_3d']`

**호출 형식**:
```python
tool_func(action, parameters, context)
```

**예시**:
```python
# Step 1
result1 = extensions_2d_to_3d_tool(
    "analyze_image",
    {"image_path": "/path/to/image.jpg"},
    {}
)

# Step 2 (의존성 포함)
result2 = extensions_2d_to_3d_tool(
    "generate_pattern",
    {"_dependency_result": result1},
    {"step_1": result1}
)
```

### 4.5 Extension Tool ↔ ChatGarment

#### 직접 통합 방식

**프로토콜**: Python 함수 호출
**클래스**: `ChatGarmentPipeline`

**호출 형식**:
```python
pipeline = ChatGarmentPipeline(device="cuda")
pipeline.load_model()
result = pipeline.analyze_image(image_path)
```

#### 마이크로서비스 방식

**프로토콜**: HTTP/HTTPS
**포트**: 9000
**엔드포인트**: `/api/v1/process`

**요청 구조**:
```python
POST /api/v1/process
Content-Type: multipart/form-data

image: <이미지 파일>
garment_id: "garment_001" (선택적)
```

**응답 구조**:
```json
{
  "status": "success",
  "garment_id": "garment_001",
  "output_dir": "/path/to/output",
  "geometry_features": "...",
  "pattern_code": "...",
  "json_spec_path": "/path/to/specification.json",
  "mesh_path": "/path/to/mesh.obj"
}
```

### 4.6 ChatGarment ↔ GarmentCodeRC

**프로토콜**: Python 함수 호출 + 서브프로세스

**함수 호출**:
```python
from llava.garment_utils_v2 import run_garmentcode_parser_float50

all_json_spec_files = run_garmentcode_parser_float50(
    all_json_spec_files,
    json_output,      # ChatGarment의 JSON 출력
    float_preds,      # ChatGarment의 Float 예측값
    saved_dir         # 출력 디렉토리
)
```

**서브프로세스 호출**:
```python
import subprocess

subprocess.run([
    sys.executable,
    "ChatGarment/run_garmentcode_sim.py",
    "--json_spec_file", pattern_json_path
], timeout=600)
```

---

## 5. 실행 시퀀스 상세

### 5.1 전체 실행 시퀀스 다이어그램

```
User          Frontend        API Server      Agent 1        Agent 2        Extension      ChatGarment    GarmentCodeRC
 │                │                │              │              │              │                │                │
 │──입력─────────>│                │              │              │              │                │                │
 │                │──HTTP POST──>│                │              │              │                │                │
 │                │                │──이미지 저장─>│              │              │                │                │
 │                │                │──Custom UI──>│              │              │                │                │
 │                │                │              │──JSONPayload─>│              │                │                │
 │                │                │              │              │              │                │                │
 │                │                │              │──[인식]───────│              │                │                │
 │                │                │              │              │              │                │                │
 │                │                │              │──[판단]───────│              │                │                │
 │                │                │              │──AbstractPlan──────────────>│              │                │
 │                │                │              │              │──ExecutionPlan 생성─────────│              │                │
 │                │                │              │<─ExecutionPlan───────────────│              │                │
 │                │                │              │              │              │                │                │
 │                │                │              │──[행동]─────────────────────────────────────│              │                │
 │                │                │              │──extensions_2d_to_3d─────────>│              │                │
 │                │                │              │              │              │──analyze_image─>│              │
 │                │                │              │              │              │<─result─────────│              │
 │                │                │              │              │              │──generate_pattern───────────────>│
 │                │                │              │              │              │<─pattern_json─────────────────────│
 │                │                │              │              │              │──convert_to_3d────────────────────────────────>│
 │                │                │              │              │              │<─mesh.obj───────────────────────────────────────│
 │                │                │              │              │              │──render_result─>│              │                │
 │                │                │              │              │              │<─render.png─────│              │                │
 │                │                │              │<─final_result─────────────────────────────────────────────────────────────────│
 │                │                │<─JSONResponse─────────────────────────────────────────────────────────────────────────────────│
 │                │<─response───────────────────────────────────────────────────────────────────────────────────────────────────────│
 │<─결과 표시───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────│
```

### 5.2 단계별 상세 시퀀스

#### Phase 1: 요청 수신 및 전처리

```
1. User → Frontend: 텍스트 + 이미지 입력
2. Frontend: FormData 생성, session_id 생성
3. Frontend → API Server: HTTP POST /api/v1/request
4. API Server: 이미지 저장 (uploads/)
5. API Server: Custom UI 호출 → JSONPayload 생성
```

#### Phase 2: Agentic AI 처리

```
6. API Server → Agent Runtime: JSONPayload 전달
7. Agent Runtime: [인식] 사용자 의도 분석
8. Agent Runtime: [판단] 추상적 계획 수립
9. Agent Runtime → F.LLM: AbstractPlan 전달
10. F.LLM: 구체적 실행 계획 생성 (JSON Steps)
11. F.LLM → Agent Runtime: ExecutionPlan 반환
```

#### Phase 3: 도구 실행

```
12. Agent Runtime: [행동] 실행 계획 파싱
13. Agent Runtime → Extension Tool: Step 1 호출 (analyze_image)
14. Extension Tool → ChatGarment: 이미지 분석 요청
15. ChatGarment: Step 1 - Geometry Features 추출
16. ChatGarment → Extension Tool: 분석 결과 반환
17. Extension Tool → Agent Runtime: Step 1 결과 반환
```

#### Phase 4: 패턴 생성

```
18. Agent Runtime → Extension Tool: Step 2 호출 (generate_pattern)
19. Extension Tool: Step 1 결과를 의존성으로 전달
20. Extension Tool → ChatGarment: 패턴 코드 생성 요청
21. ChatGarment: Step 2 - Sewing Pattern Code 생성
22. ChatGarment → GarmentCodeRC: 패턴 JSON 생성 요청
23. GarmentCodeRC: 패턴 JSON 파일 생성
24. GarmentCodeRC → Extension Tool: 패턴 경로 반환
25. Extension Tool → Agent Runtime: Step 2 결과 반환
```

#### Phase 5: 3D 변환

```
26. Agent Runtime → Extension Tool: Step 3 호출 (convert_to_3d)
27. Extension Tool: Step 2 결과를 의존성으로 전달
28. Extension Tool → GarmentCodeRC: 3D 변환 요청
29. GarmentCodeRC: 물리 시뮬레이션 실행
30. GarmentCodeRC: 3D 메시 생성 (.obj 파일)
31. GarmentCodeRC → Extension Tool: 메시 경로 반환
32. Extension Tool → Agent Runtime: Step 3 결과 반환
```

#### Phase 6: 렌더링 및 결과 반환

```
33. Agent Runtime → Extension Tool: Step 4 호출 (render_result)
34. Extension Tool: Step 3 결과를 의존성으로 전달
35. Extension Tool: 렌더링 이미지 생성
36. Extension Tool → Agent Runtime: Step 4 결과 반환
37. Agent Runtime: 최종 결과 구조화
38. Agent Runtime → API Server: Final Result 반환
39. API Server: JSONResponse 생성
40. API Server → Frontend: HTTP Response
41. Frontend: 결과 시각화 (3D 뷰어)
42. Frontend → User: 결과 표시
```

---

## 6. 핵심 통합 포인트 상세

### 6.1 Agent 1 ↔ Agent 2 통합

**통신 방식**: Python 함수 호출

**호출 코드**:
```python
# agent_runtime.py
execution_plan = self.agent2.generate_execution_plan(
    abstract_plan.dict(),
    context=input_data,
    rag_context=None,
    user_text=input_data.get("text"),
    image_path=input_data.get("image_path")
)
```

**데이터 흐름**:
```
AbstractPlan (Dict) 
    ↓
F.LLM.generate_execution_plan()
    ↓
ExecutionPlan (Pydantic Model)
    ↓
Agent Runtime._execute_plan()
```

### 6.2 Extension Tool ↔ ChatGarment 통합

#### 직접 통합 방식

**초기화**:
```python
# extensions.py
self.chatgarment_pipeline = ChatGarmentPipeline(device=self.device)
self.chatgarment_pipeline.load_model()
```

**호출**:
```python
result = self.chatgarment_pipeline.analyze_image(image_path)
```

#### 마이크로서비스 방식

**환경 변수 설정**:
```python
USE_CHATGARMENT_SERVICE = "true"
CHATGARMENT_SERVICE_URL = "http://localhost:9000"
```

**HTTP 호출**:
```python
# extensions_service.py
response = requests.post(
    f"{CHATGARMENT_SERVICE_URL}/api/v1/process",
    files={"image": open(image_path, "rb")},
    data={"garment_id": garment_id}
)
result = response.json()
```

### 6.3 ChatGarment ↔ GarmentCodeRC 통합

**패턴 생성**:
```python
# chatgarment_integration.py
from llava.garment_utils_v2 import run_garmentcode_parser_float50

all_json_spec_files = run_garmentcode_parser_float50(
    all_json_spec_files,
    json_output,      # ChatGarment Step 2 출력
    float_preds,      # ChatGarment Float 예측값
    saved_dir
)
```

**3D 변환**:
```python
# chatgarment_integration.py
sim_script = chatgarment_path / "run_garmentcode_sim.py"

subprocess.run([
    sys.executable,
    str(sim_script),
    "--json_spec_file", json_spec_path_abs
], cwd=str(project_root), timeout=600)
```

---

## 7. 에러 처리 및 복구 메커니즘

### 7.1 자기 수정 루프 (Self-Correction Loop)

**위치**: Agent Runtime (Agent 1)

**동작 방식**:
```python
def _self_correction_loop(
    self,
    execution_plan: ExecutionPlan,
    execution_result: Dict[str, Any],
    memory: ShortTermMemory,
    retry_count: int = 0
) -> Dict[str, Any]:
    # 결과 평가
    evaluation = self._evaluate_result(execution_result)
    
    if evaluation["success"]:
        return {"status": "success", "data": execution_result}
    
    # 실패 시 재시도
    if retry_count < self.max_retries:
        retry_result = self._execute_plan(execution_plan, memory)
        return self._self_correction_loop(
            execution_plan, retry_result, memory, retry_count + 1
        )
    else:
        return {"status": "failed", "data": execution_result}
```

**재시도 조건**:
- 단계 실행 실패
- 결과 검증 실패
- 타임아웃 발생

**최대 재시도 횟수**: 기본값 1회 (설정 가능)

### 7.2 Fallback 메커니즘

#### ChatGarment 모델 로딩 실패 시

**Fallback**: Mock 모드로 전환

```python
if not self.model_loaded:
    print("⚠️ 모델이 로드되지 않아 Mock 모드로 동작합니다.")
    return self._mock_analyze_image(image_path, text_description)
```

#### InternVL2 모델 로딩 실패 시

**Fallback**: 규칙 기반 모드로 전환

```python
if not self.llm_model:
    print("⚠️ InternVL2 모델 로딩 실패. 규칙 기반 모드로 전환합니다.")
    enhanced_plan = abstract_plan  # LLM 없이 규칙 기반 계획 생성
```

---

## 8. 성능 최적화 포인트

### 8.1 병렬 처리 가능 영역

현재는 순차 실행이지만, 향후 병렬화 가능한 영역:

- **독립적인 단계**: 의존성이 없는 단계는 병렬 실행 가능
- **이미지 전처리**: 여러 이미지 동시 처리
- **배치 추론**: 여러 요청을 배치로 묶어 처리

### 8.2 캐싱 전략

**이미지 분석 결과 캐싱**:
- 동일 이미지에 대한 분석 결과 캐싱
- 해시 기반 캐시 키 사용

**패턴 생성 결과 캐싱**:
- 동일 분석 결과에 대한 패턴 캐싱

### 8.3 리소스 관리

**모델 로딩 전략**:
- 지연 로딩 (Lazy Loading)
- 모델 공유 (여러 요청 간 모델 인스턴스 공유)

**메모리 관리**:
- 중간 결과 정리
- GPU 메모리 최적화

---

## 9. 확장성 고려사항

### 9.1 수평 확장 (Horizontal Scaling)

**마이크로서비스 아키텍처**:
- ChatGarment Service를 독립 서버로 분리
- 여러 GPU 서버에 분산 배치
- 로드 밸런서를 통한 요청 분산

### 9.2 수직 확장 (Vertical Scaling)

**리소스 증설**:
- GPU 메모리 증가
- CPU 코어 수 증가
- 더 큰 모델 사용 가능

### 9.3 도구 확장

**새로운 도구 추가**:
```python
# 도구 등록
agent_runtime.register_tool("new_tool_name", new_tool_function)

# 실행 계획에 자동 포함
execution_plan = agent2.generate_execution_plan(...)
# new_tool_name이 필요한 경우 자동으로 steps에 포함
```

---

## 10. 결론

본 아키텍처 다이어그램은 Fashion Agentic AI System의 전체 워크플로우를 명확하게 보여줍니다. 주요 특징:

1. **계층화된 구조**: 각 계층이 명확한 역할을 담당
2. **유연한 통합**: 직접 통합과 마이크로서비스 방식 모두 지원
3. **의존성 관리**: 단계 간 의존성을 자동으로 관리
4. **확장 가능성**: 새로운 도구와 기능을 쉽게 추가 가능
5. **에러 복구**: 자기 수정 루프를 통한 자동 재시도

이러한 구조를 통해 복잡한 의류 생성 작업을 자율적으로 수행할 수 있는 지능형 시스템을 구현하였습니다.

