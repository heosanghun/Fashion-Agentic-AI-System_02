# ChatGarment 시스템 상세 가이드

## 📋 목차
1. [입력 데이터](#1-입력-데이터)
2. [데이터 정의 및 명세서](#2-데이터-정의-및-명세서)
3. [시스템 동작 원리](#3-시스템-동작-원리)
4. [코드별 역할 상세 설명](#4-코드별-역할-상세-설명)
5. [입력 → 3D 변환 → 출력 전체 흐름](#5-입력--3d-변환--출력-전체-흐름)
6. [결과물 파일 형식 및 저장 위치](#6-결과물-파일-형식-및-저장-위치)

---

## 1. 입력 데이터

### 1.1 입력 데이터 종류

ChatGarment 시스템은 **두 가지 형태의 입력**을 받습니다:

#### 1.1.1 텍스트 입력 (Text Input)
- **형식**: 문자열 (String)
- **예시**: 
  - "이 옷을 3D로 만들어줘"
  - "이 옷을 입혀줘"
  - "가상 피팅 해줘"
- **용도**: 사용자의 의도와 요청을 전달

#### 1.1.2 이미지 입력 (Image Input)
- **형식**: 이미지 파일 (JPG, PNG, JPEG 등)
- **크기**: 제한 없음 (시스템에서 자동으로 정사각형으로 패딩 처리)
- **내용**: 사람이 의류를 입고 있는 사진
- **예시**: 
  - 상의를 입은 모델 사진
  - 하의를 입은 모델 사진
  - 전체 의상을 입은 모델 사진
- **용도**: 의류의 기하학적 특징을 분석하기 위한 시각적 정보

### 1.2 입력 데이터 전달 방식

#### API를 통한 입력
```python
# Form 데이터로 전달
{
    "text": "이 옷을 3D로 만들어줘",      # 선택적
    "image": <이미지 파일>,                # 선택적 (하지만 텍스트 또는 이미지 중 하나는 필수)
    "user_id": "user123",                 # 선택적
    "session_id": "session456"            # 선택적 (없으면 자동 생성)
}
```

#### 파일 경로를 통한 입력
```python
{
    "text": "이 옷을 3D로 만들어줘",
    "image_path": "/path/to/garment_image.jpg",
    "user_id": "user123",
    "session_id": "session456"
}
```

---

## 2. 데이터 정의 및 명세서

### 2.1 입력 데이터 스키마

#### UserInput 모델
```python
class UserInput(BaseModel):
    text: Optional[str] = None              # 사용자 텍스트 입력
    image_path: Optional[str] = None         # 이미지 파일 경로
    image_data: Optional[bytes] = None       # 이미지 바이너리 데이터
    user_id: Optional[str] = None            # 사용자 ID
    session_id: Optional[str] = None          # 세션 ID
```

#### JSONPayload 모델 (시스템 내부 처리용)
```python
class JSONPayload(BaseModel):
    timestamp: str                           # 요청 시각 (ISO 형식)
    user_id: Optional[str]                   # 사용자 ID
    session_id: Optional[str]                # 세션 ID
    input_data: Dict                         # 실제 입력 데이터
    metadata: Dict = {}                      # 메타데이터
```

### 2.2 중간 데이터 형식

#### Step 1: Geometry Features (기하학적 특징)
```json
{
    "upper_garment": ["hoodie", "long sleeves", "with a hood", "wide garment"],
    "lower_garment": ["jeans", "long legs", "narrow garment"]
}
```
또는
```json
{
    "wholebody_garment": ["dress", "long length", "sleeveless", "wide garment"]
}
```

#### Step 2: Sewing Pattern Code (재봉 패턴 코드)
```json
{
    "upperbody_garment": {
        "front": {
            "width": 50.0,
            "height": 70.0,
            "seams": ["shoulder", "side", "bottom"]
        },
        "back": {
            "width": 50.0,
            "height": 70.0,
            "seams": ["shoulder", "side", "bottom"]
        },
        "sleeves": {
            "length": 60.0,
            "width": 30.0,
            "seams": ["armhole", "side", "cuff"]
        }
    },
    "lowerbody_garment": {
        // ... 하의 정보
    }
}
```

#### Float Predictions (Float 예측값)
- **형식**: NumPy 배열 또는 리스트
- **용도**: GarmentCode 파라미터의 정확한 수치값
- **예시**: `[0.5, 0.3, 0.8, ...]` (50개의 float 값)

### 2.3 출력 데이터 형식

#### Pattern Specification JSON
```json
{
    "garment_type": "hoodie",
    "components": ["front", "back", "sleeves", "hood"],
    "specification": {
        "front": {
            "width": 50.0,
            "height": 70.0,
            "seams": ["shoulder", "side", "bottom"],
            "vertices": [[x1, y1], [x2, y2], ...],
            "edges": [[v1, v2], [v2, v3], ...]
        },
        // ... 다른 컴포넌트들
    },
    "version": "1.0",
    "created_by": "ChatGarment"
}
```

#### 3D Mesh 파일 (OBJ 형식)
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

---

## 3. 시스템 동작 원리

### 3.1 전체 아키텍처

ChatGarment 시스템은 **Agentic AI 프레임워크**를 기반으로 동작합니다:

```
사용자 입력
    ↓
[Custom UI] → 입력 데이터 구조화
    ↓
[Agent Runtime (Agent 1)] → 요청 분석 및 계획 수립
    ↓
[F.LLM (Agent 2)] → 구체적 실행 계획 생성
    ↓
[Extensions Tool] → 실제 작업 실행
    ├─ Step 1: 이미지 분석 (ChatGarment 모델)
    ├─ Step 2: 패턴 생성 (GarmentCode)
    ├─ Step 3: 3D 변환 (GarmentCodeRC)
    └─ Step 4: 렌더링
    ↓
결과 반환
```

### 3.2 단계별 동작 원리

#### 3.2.1 입력 처리 단계 (Custom UI)
**파일**: `agentic_system/core/custom_ui.py`

1. **입력 검증**: 텍스트 또는 이미지 중 하나는 필수
2. **이미지 저장**: 업로드된 이미지를 `uploads/` 디렉토리에 저장
3. **데이터 구조화**: UserInput을 JSONPayload로 변환
4. **세션 관리**: session_id가 없으면 자동 생성

#### 3.2.2 요청 분석 단계 (Agent Runtime)
**파일**: `agentic_system/core/agent_runtime.py`

1. **의도 분석**: 사용자 요청을 분석하여 작업 유형 결정
   - "입혀줘", "3D로 만들어줘" → `3d_generation`
   - "추천해줘", "찾아줘" → `garment_recommendation`
2. **추상적 계획 수립**: 큰 그림의 작업 계획 생성
3. **Agent 2 호출**: 구체적 실행 계획 생성을 위해 F.LLM 호출

#### 3.2.3 실행 계획 생성 단계 (F.LLM)
**파일**: `agentic_system/core/f_llm.py`

1. **InternVL2-8B 모델 사용**: 멀티모달 입력 처리
2. **실행 단계 생성**: 4단계 실행 계획 생성
   - Step 1: `analyze_image` (이미지 분석)
   - Step 2: `generate_pattern` (패턴 생성)
   - Step 3: `convert_to_3d` (3D 변환)
   - Step 4: `render_result` (렌더링)
3. **의존성 설정**: 각 단계의 의존성 관계 정의

#### 3.2.4 실제 작업 실행 단계 (Extensions Tool)
**파일**: `agentic_system/tools/extensions.py`

각 단계가 순차적으로 실행되며, 이전 단계의 결과가 다음 단계의 입력으로 사용됩니다.

---

## 4. 코드별 역할 상세 설명

### 4.1 API 서버 (`agentic_system/api/main.py`)

**역할**: 사용자 요청을 받아 시스템에 전달하고 결과를 반환

**주요 함수**:
- `process_request()`: POST 요청 처리
  - 이미지 파일 저장 (`uploads/` 디렉토리)
  - Custom UI를 통한 입력 처리
  - Agent Runtime을 통한 요청 처리
  - 결과 포맷팅 및 반환

**코드 흐름**:
```python
# 1. 이미지 파일 저장
if image:
    image_path = upload_dir / f"{session_id}_{image.filename}"
    with open(image_path, "wb") as f:
        f.write(await image.read())

# 2. Custom UI 입력 처리
payload = custom_ui.process_user_input(
    text=text,
    image_path=image_path,
    user_id=user_id,
    session_id=session_id
)

# 3. Agent Runtime 요청 처리
result = agent_runtime.process_request(
    payload.dict(),
    session_id=session_id
)

# 4. 결과 포맷팅
response = custom_ui.format_output(result)
```

### 4.2 Custom UI (`agentic_system/core/custom_ui.py`)

**역할**: 사용자 입력을 시스템이 이해할 수 있는 형식으로 변환

**주요 함수**:
- `process_user_input()`: 입력 데이터 구조화
  - 입력 검증 (텍스트 또는 이미지 필수)
  - 이미지 데이터 처리
  - JSONPayload 생성
  - 세션 ID 생성

**코드 흐름**:
```python
# 입력 데이터 구조화
input_data = {
    "text": text,
    "image_path": image_path,
    "has_image": bool(image_path or image_data)
}

# JSONPayload 생성
payload = JSONPayload(
    timestamp=datetime.now().isoformat(),
    user_id=user_id,
    session_id=session_id or self._generate_session_id(),
    input_data=input_data,
    metadata=metadata
)
```

### 4.3 Agent Runtime (`agentic_system/core/agent_runtime.py`)

**역할**: 전체 프로세스를 오케스트레이션하는 핵심 엔진

**주요 함수**:
- `process_request()`: 전체 요청 처리 프로세스
  1. **인식 (Perception)**: `_analyze_user_intent()` - 사용자 의도 분석
  2. **판단 (Judgment)**: `_create_abstract_plan()` - 추상적 계획 수립
  3. **행동 (Action)**: `_execute_plan()` - 도구 실행
  4. **자기 수정**: `_self_correction_loop()` - 결과 검증 및 재시도

**코드 흐름**:
```python
# 1. 사용자 의도 분석
user_intent = self._analyze_user_intent(payload)
# 결과: {"type": "3d_generation", "confidence": 0.9, ...}

# 2. 추상적 계획 수립
abstract_plan = self._create_abstract_plan(user_intent, payload, memory)
# 결과: AbstractPlan(plan_type="3d_generation", steps=[...], ...)

# 3. Agent 2에게 실행 계획 생성 요청
execution_plan = self.agent2.generate_execution_plan(
    abstract_plan.dict(),
    context=input_data
)

# 4. 실행 계획에 따라 도구 실행
execution_result = self._execute_plan(execution_plan, memory)
```

### 4.4 F.LLM (`agentic_system/core/f_llm.py`)

**역할**: 추상적 계획을 구체적인 실행 단계로 변환

**주요 함수**:
- `generate_execution_plan()`: 실행 계획 생성
  - InternVL2-8B 모델 사용
  - 4단계 실행 계획 생성
  - 의존성 관계 설정

**생성되는 실행 계획**:
```python
[
    {
        "step_id": 1,
        "tool": "extensions_2d_to_3d",
        "action": "analyze_image",
        "parameters": {
            "image_path": "...",
            "text_description": "..."
        },
        "dependencies": []
    },
    {
        "step_id": 2,
        "tool": "extensions_2d_to_3d",
        "action": "generate_pattern",
        "parameters": {},
        "dependencies": [1]  # Step 1의 결과 필요
    },
    {
        "step_id": 3,
        "tool": "extensions_2d_to_3d",
        "action": "convert_to_3d",
        "parameters": {},
        "dependencies": [2]  # Step 2의 결과 필요
    },
    {
        "step_id": 4,
        "tool": "extensions_2d_to_3d",
        "action": "render_result",
        "parameters": {},
        "dependencies": [3]  # Step 3의 결과 필요
    }
]
```

### 4.5 Extensions Tool (`agentic_system/tools/extensions.py`)

**역할**: 실제 2D→3D 변환 작업을 수행하는 핵심 도구

**주요 클래스**: `Extensions2DTo3D`

#### 4.5.1 Step 1: 이미지 분석 (`_analyze_image`)

**역할**: ChatGarment 모델을 사용하여 이미지에서 의류의 기하학적 특징 추출

**동작 과정**:
1. **모델 로딩**: ChatGarment 모델 로딩 (지연 로딩)
2. **이미지 전처리**:
   - PIL Image로 로딩
   - RGB로 변환
   - 정사각형으로 패딩 (필요시)
   - Vision Tower의 image_processor로 전처리
3. **프롬프트 구성**:
   ```
   "Can you describe the geometry features of the garments 
   worn by the model in the Json format?"
   ```
4. **모델 추론**:
   - Vision Encoder로 이미지 인코딩
   - Language Model로 텍스트 생성
   - JSON 형식의 기하학적 특징 추출
5. **결과 파싱**:
   - JSON 수정 및 검증
   - Float 예측값 추출

**코드 흐름**:
```python
# 1. 이미지 로딩 및 전처리
image = Image.open(image_path).convert('RGB')
image_clip = processor.preprocess(image, return_tensors='pt')['pixel_values'][0]
image_clip = image_clip.unsqueeze(0).to(device).bfloat16()

# 2. 프롬프트 구성
question = 'Can you describe the geometry features of the garments worn by the model in the Json format?'
prompt = DEFAULT_IMAGE_TOKEN + "\n" + question
input_ids = tokenizer_image_token(prompt, tokenizer, return_tensors="pt")

# 3. 모델 추론
with torch.no_grad():
    output_ids, float_preds, seg_token_mask = model.evaluate(
        image_clip, image_clip, input_ids,
        max_new_tokens=2048,
        tokenizer=tokenizer
    )

# 4. 결과 파싱
text_output = tokenizer.decode(output_ids, skip_special_tokens=False)
json_output = repair_json(text_output, return_objects=True)
```

**출력 형식**:
```python
{
    "status": "success",
    "analysis": {
        "upper_garment": ["hoodie", "long sleeves", "with a hood"],
        "lower_garment": ["jeans", "long legs"]
    },
    "text_output": "...",
    "float_preds": [[0.5, 0.3, 0.8, ...]],  # 50개의 float 값
    "image_path": "...",
    "message": "이미지 분석이 완료되었습니다."
}
```

#### 4.5.2 Step 2: 패턴 생성 (`_generate_pattern`)

**역할**: 분석 결과를 기반으로 2D 재봉 패턴 생성

**동작 과정**:
1. **이전 단계 결과 사용**: Step 1의 분석 결과와 Float 예측값 사용
2. **GarmentCode 파서 호출**: `run_garmentcode_parser_float50()` 함수 사용
3. **패턴 JSON 생성**: 
   - 컴포넌트별 정점(vertices) 좌표
   - 엣지(edges) 연결 정보
   - 시접(seams) 정보
4. **Specification JSON 저장**: `outputs/patterns/valid_garment_{garment_id}/` 디렉토리에 저장

**코드 흐름**:
```python
# 1. 이전 단계 결과 가져오기
analysis = parameters.get("_dependency_result") or context.get("step_1")
json_output = analysis.get("analysis")
float_preds = analysis.get("float_preds")

# 2. GarmentCode 파서 호출
all_json_spec_files = run_garmentcode_parser_float50(
    all_json_spec_files,
    json_output,
    float_preds,
    saved_dir
)

# 3. 생성된 파일 경로 반환
pattern_json_path = os.path.join(
    saved_dir, 
    f'valid_garment_{garment_name}',
    f'valid_garment_{garment_name}_specification.json'
)
```

**출력 형식**:
```python
{
    "status": "success",
    "pattern_path": "outputs/patterns/valid_garment_001/valid_garment_001_specification.json",
    "pattern_info": {
        "type": "hoodie",
        "components": ["front", "back", "sleeves", "hood"]
    },
    "message": "패턴 생성이 완료되었습니다."
}
```

#### 4.5.3 Step 3: 3D 변환 (`_convert_to_3d`)

**역할**: 2D 패턴을 3D 메시로 변환

**동작 과정**:
1. **이전 단계 결과 사용**: Step 2의 패턴 JSON 파일 경로 사용
2. **GarmentCodeRC 시뮬레이션 실행**:
   - `run_garmentcode_sim.py` 스크립트를 서브프로세스로 실행
   - 패턴 JSON을 입력으로 받아 3D 메시 생성
3. **3D 메시 파일 생성**: `.obj` 형식의 3D 메시 파일 생성

**코드 흐름**:
```python
# 1. 이전 단계 결과 가져오기
pattern_result = parameters.get("_dependency_result") or context.get("step_2")
pattern_json_path = pattern_result.get("pattern_path")

# 2. GarmentCodeRC 시뮬레이션 실행
sim_script = project_root / "ChatGarment" / "run_garmentcode_sim.py"
command = f'python "{sim_script}" --json_spec_file "{pattern_json_path}"'

result = subprocess.run(
    command,
    shell=True,
    capture_output=True,
    text=True,
    cwd=str(project_root),
    timeout=600  # 10분 타임아웃
)

# 3. 생성된 메시 파일 찾기
pattern_dir = os.path.dirname(pattern_json_path)
mesh_path = os.path.join(pattern_dir, f"{os.path.basename(pattern_dir)}_sim.obj")
```

**GarmentCodeRC 내부 동작** (`ChatGarment/run_garmentcode_sim.py`):
1. **Box Mesh 생성**: 패턴을 기반으로 초기 3D 박스 메시 생성
2. **물리 시뮬레이션**: Qualoth 엔진을 사용한 의류 시뮬레이션
   - 중력, 마찰, 충돌 등 물리 효과 적용
   - 인체 모델에 맞춰 의류가 자연스럽게 떨어지도록 시뮬레이션
3. **메시 최적화**: 시뮬레이션 결과를 최적화된 메시로 변환
4. **OBJ 파일 저장**: 최종 3D 메시를 `.obj` 형식으로 저장

**출력 형식**:
```python
{
    "status": "success",
    "mesh_path": "outputs/patterns/valid_garment_001/valid_garment_001_sim.obj",
    "mesh_info": {
        "format": "obj",
        "path": "..."
    },
    "message": "3D 변환이 완료되었습니다."
}
```

#### 4.5.4 Step 4: 렌더링 (`_render_result`)

**역할**: 3D 모델을 시각화하여 이미지로 렌더링

**현재 상태**: Mock 모드 (실제 렌더링은 향후 구현 예정)

**출력 형식**:
```python
{
    "status": "success",
    "render_path": "outputs/renders/garment_render.png",
    "visualization": {
        "image_path": "outputs/renders/garment_render.png",
        "mesh_path": "outputs/patterns/valid_garment_001/valid_garment_001_sim.obj"
    },
    "message": "렌더링이 완료되었습니다."
}
```

### 4.6 ChatGarment 통합 모듈 (`agentic_system/tools/chatgarment_integration.py`)

**역할**: ChatGarment 모델의 완전한 파이프라인을 제공

**주요 클래스**: `ChatGarmentPipeline`

**주요 함수**:
- `load_model()`: ChatGarment 모델 로딩
- `process_image_to_garment()`: 전체 파이프라인 실행
  1. Step 1: Geometry features 추출
  2. Step 2: Sewing pattern code 생성
  3. GarmentCode 패턴 생성
  4. 3D 변환 (GarmentCodeRC)

**코드 흐름**:
```python
# 1. 모델 로딩
pipeline = ChatGarmentPipeline(device="cuda")
pipeline.load_model()

# 2. 전체 파이프라인 실행
result = pipeline.process_image_to_garment(
    image_path="path/to/image.jpg",
    garment_id="test_001"
)

# 결과:
# {
#     "status": "success",
#     "garment_id": "test_001",
#     "output_dir": "outputs/garments/valid_garment_test_001",
#     "geometry_features": "...",
#     "pattern_code": "...",
#     "json_output": {...},
#     "float_preds": [...],
#     "json_spec_path": "...",
#     "mesh_path": "..."
# }
```

---

## 5. 입력 → 3D 변환 → 출력 전체 흐름

### 5.1 전체 파이프라인 흐름도

```
[사용자 입력]
    │
    ├─ 텍스트: "이 옷을 3D로 만들어줘"
    └─ 이미지: garment_image.jpg
    │
    ↓
[API 서버] (main.py)
    │
    ├─ 이미지 파일 저장 → uploads/session_xxx_garment_image.jpg
    └─ Custom UI 입력 처리
    │
    ↓
[Custom UI] (custom_ui.py)
    │
    ├─ 입력 데이터 구조화
    └─ JSONPayload 생성
    │
    ↓
[Agent Runtime] (agent_runtime.py)
    │
    ├─ 사용자 의도 분석 → "3d_generation"
    ├─ 추상적 계획 수립
    └─ Agent 2 (F.LLM) 호출
    │
    ↓
[F.LLM] (f_llm.py)
    │
    ├─ InternVL2-8B 모델 사용
    └─ 4단계 실행 계획 생성
    │
    ↓
[Extensions Tool] (extensions.py)
    │
    ├─ Step 1: 이미지 분석 (analyze_image)
    │   │
    │   ├─ ChatGarment 모델 로딩
    │   ├─ 이미지 전처리
    │   ├─ Vision Encoder로 이미지 인코딩
    │   ├─ Language Model로 텍스트 생성
    │   └─ JSON 파싱
    │   │
    │   출력: {
    │       "analysis": {"upper_garment": [...], "lower_garment": [...]},
    │       "float_preds": [[...]]
    │   }
    │
    ├─ Step 2: 패턴 생성 (generate_pattern)
    │   │
    │   ├─ Step 1 결과 사용
    │   ├─ GarmentCode 파서 호출
    │   └─ 패턴 JSON 생성
    │   │
    │   출력: {
    │       "pattern_path": "outputs/patterns/valid_garment_001/..._specification.json"
    │   }
    │
    ├─ Step 3: 3D 변환 (convert_to_3d)
    │   │
    │   ├─ Step 2 결과 사용
    │   ├─ GarmentCodeRC 시뮬레이션 실행
    │   │   ├─ Box Mesh 생성
    │   │   ├─ 물리 시뮬레이션 (Qualoth)
    │   │   └─ 메시 최적화
    │   └─ OBJ 파일 저장
    │   │
    │   출력: {
    │       "mesh_path": "outputs/patterns/valid_garment_001/..._sim.obj"
    │   }
    │
    └─ Step 4: 렌더링 (render_result)
        │
        └─ 3D 모델 렌더링 (현재 Mock)
        │
        출력: {
            "render_path": "outputs/renders/garment_render.png"
        }
    │
    ↓
[최종 결과 반환]
    │
    └─ JSON 응답
```

### 5.2 단계별 상세 흐름

#### Step 1: 이미지 분석 상세

```
입력 이미지 (garment_image.jpg)
    ↓
[이미지 로딩]
    ├─ PIL Image.open()
    └─ RGB로 변환
    ↓
[이미지 전처리]
    ├─ 정사각형으로 패딩 (필요시)
    └─ Vision Tower의 image_processor로 전처리
    ↓
[Vision Encoder]
    ├─ CLIP Vision Tower 사용
    └─ 이미지를 임베딩 벡터로 변환
    ↓
[Language Model]
    ├─ 프롬프트: "Can you describe the geometry features..."
    ├─ 이미지 임베딩 + 텍스트 토큰 결합
    └─ 텍스트 생성 (JSON 형식)
    ↓
[결과 파싱]
    ├─ JSON 수정 (repair_json)
    └─ Float 예측값 추출
    ↓
출력:
{
    "analysis": {
        "upper_garment": ["hoodie", "long sleeves", "with a hood"],
        "lower_garment": ["jeans", "long legs"]
    },
    "float_preds": [[0.5, 0.3, 0.8, ...]]
}
```

#### Step 2: 패턴 생성 상세

```
Step 1 결과
    ├─ analysis: JSON 형식의 기하학적 특징
    └─ float_preds: 50개의 float 값
    ↓
[GarmentCode 파서]
    ├─ JSON을 파싱하여 컴포넌트 추출
    ├─ Float 값을 파라미터로 사용
    └─ 각 컴포넌트의 정점 좌표 계산
    ↓
[패턴 생성]
    ├─ Front 패널: 정점 좌표, 엣지, 시접
    ├─ Back 패널: 정점 좌표, 엣지, 시접
    ├─ Sleeves: 정점 좌표, 엣지, 시접
    └─ Hood: 정점 좌표, 엣지, 시접
    ↓
[Specification JSON 저장]
    └─ outputs/patterns/valid_garment_001/
        └─ valid_garment_001_specification.json
    ↓
출력:
{
    "pattern_path": "outputs/patterns/valid_garment_001/..._specification.json"
}
```

#### Step 3: 3D 변환 상세

```
Step 2 결과 (패턴 JSON 파일)
    ↓
[GarmentCodeRC 시뮬레이션]
    ├─ 패턴 JSON 로딩
    └─ Box Mesh 생성
        ├─ 각 패널을 3D 박스로 변환
        └─ 초기 메시 생성
    ↓
[물리 시뮬레이션]
    ├─ Qualoth 엔진 사용
    ├─ 중력 적용
    ├─ 마찰 적용
    ├─ 충돌 감지 (인체 모델과의 충돌)
    └─ 시뮬레이션 실행 (여러 프레임)
    ↓
[메시 최적화]
    ├─ 시뮬레이션 결과를 최적화
    └─ 정점 수 조정
    ↓
[OBJ 파일 저장]
    └─ outputs/patterns/valid_garment_001/
        └─ valid_garment_001_sim.obj
    ↓
출력:
{
    "mesh_path": "outputs/patterns/valid_garment_001/..._sim.obj"
}
```

---

## 6. 결과물 파일 형식 및 저장 위치

### 6.1 저장 디렉토리 구조

```
ChatGarment/
├── uploads/                          # 입력 이미지 저장 위치
│   └── session_xxx_garment_image.jpg
│
├── outputs/                          # 모든 출력 파일 저장 위치
│   ├── patterns/                     # 패턴 파일 저장 위치
│   │   └── valid_garment_{id}/
│   │       ├── valid_garment_{id}_specification.json
│   │       ├── valid_garment_{id}_sim.obj
│   │       ├── output.txt            # 분석 결과 텍스트
│   │       └── gt_image.png          # 원본 이미지 복사본
│   │
│   ├── 3d_models/                    # 3D 모델 파일 (Mock 모드)
│   │   └── garment.obj
│   │
│   ├── renders/                      # 렌더링 결과 (Mock 모드)
│   │   └── garment_render.png
│   │
│   └── garments/                    # 전체 파이프라인 결과 (ChatGarmentPipeline 사용 시)
│       └── valid_garment_{id}/
│           ├── valid_garment_{id}_specification.json
│           ├── valid_garment_{id}_sim.obj
│           ├── output.txt
│           └── gt_image.png
```

### 6.2 파일 형식 상세 설명

#### 6.2.1 입력 이미지
- **위치**: `uploads/session_{session_id}_{filename}`
- **형식**: JPG, PNG, JPEG 등
- **예시**: `uploads/session_1762425938_TShirt.jpg`

#### 6.2.2 패턴 Specification JSON
- **위치**: `outputs/patterns/valid_garment_{id}/valid_garment_{id}_specification.json`
- **형식**: JSON
- **내용**:
  ```json
  {
      "garment_type": "hoodie",
      "components": ["front", "back", "sleeves", "hood"],
      "specification": {
          "front": {
              "width": 50.0,
              "height": 70.0,
              "seams": ["shoulder", "side", "bottom"],
              "vertices": [[x1, y1], [x2, y2], ...],
              "edges": [[v1, v2], [v2, v3], ...]
          },
          // ... 다른 컴포넌트들
      }
  }
  ```

#### 6.2.3 3D Mesh 파일 (OBJ 형식)
- **위치**: `outputs/patterns/valid_garment_{id}/valid_garment_{id}_sim.obj`
- **형식**: OBJ (Wavefront Object)
- **내용**:
  ```
  # OBJ 파일 헤더
  v -1.0 -1.0 -1.0    # 정점 (vertex) - x, y, z 좌표
  v 1.0 -1.0 -1.0
  v 1.0 1.0 -1.0
  ...
  f 1 2 3 4           # 면 (face) - 정점 인덱스
  f 5 6 7 8
  ...
  ```
- **용도**: 
  - 3D 뷰어에서 열어볼 수 있음 (Blender, MeshLab 등)
  - 가상 피팅 시스템에서 사용
  - 3D 프린팅 가능

#### 6.2.4 분석 결과 텍스트 파일
- **위치**: `outputs/patterns/valid_garment_{id}/output.txt`
- **형식**: 텍스트 파일
- **내용**:
  ```
  ============================================================
  Step 1: Geometry Features
  ============================================================
  [프롬프트와 응답]
  
  ============================================================
  Step 2: Sewing Pattern Code
  ============================================================
  [프롬프트와 응답]
  
  ============================================================
  Parsed JSON
  ============================================================
  [파싱된 JSON]
  ```

#### 6.2.5 원본 이미지 복사본
- **위치**: `outputs/patterns/valid_garment_{id}/gt_image.png`
- **형식**: PNG
- **용도**: 결과와 비교하기 위한 원본 이미지

### 6.3 파일 접근 방법

#### API를 통한 파일 접근
```python
# 파일 제공 엔드포인트
GET /api/v1/file?path=outputs/patterns/valid_garment_001/valid_garment_001_sim.obj
```

#### 직접 파일 시스템 접근
```python
# Python에서 파일 읽기
import json

# 패턴 JSON 읽기
with open("outputs/patterns/valid_garment_001/valid_garment_001_specification.json", "r", encoding="utf-8") as f:
    pattern_data = json.load(f)

# OBJ 파일 읽기
with open("outputs/patterns/valid_garment_001/valid_garment_001_sim.obj", "r") as f:
    obj_content = f.read()
```

### 6.4 결과물 사용 예시

#### 3D 모델 뷰어에서 열기
```python
# Blender에서 열기
import bpy

# OBJ 파일 임포트
bpy.ops.import_scene.obj(filepath="outputs/patterns/valid_garment_001/valid_garment_001_sim.obj")
```

#### 웹에서 3D 모델 표시
```html
<!-- Three.js 사용 예시 -->
<script src="https://cdn.jsdelivr.net/npm/three@0.150.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.150.0/examples/js/loaders/OBJLoader.js"></script>

<script>
    const loader = new THREE.OBJLoader();
    loader.load(
        'outputs/patterns/valid_garment_001/valid_garment_001_sim.obj',
        function (object) {
            scene.add(object);
        }
    );
</script>
```

---

## 7. 요약

### 7.1 입력 데이터
- **텍스트**: 사용자 요청 (선택적)
- **이미지**: 의류를 입은 모델 사진 (선택적, 하지만 텍스트 또는 이미지 중 하나는 필수)

### 7.2 처리 과정
1. **입력 처리**: Custom UI가 입력 데이터를 구조화
2. **요청 분석**: Agent Runtime이 사용자 의도 분석
3. **계획 수립**: F.LLM이 구체적 실행 계획 생성
4. **작업 실행**: Extensions Tool이 4단계 작업 수행
   - 이미지 분석 → 패턴 생성 → 3D 변환 → 렌더링

### 7.3 출력 결과
- **패턴 JSON**: `outputs/patterns/valid_garment_{id}/..._specification.json`
- **3D 메시**: `outputs/patterns/valid_garment_{id}/..._sim.obj`
- **분석 결과**: `outputs/patterns/valid_garment_{id}/output.txt`
- **원본 이미지**: `outputs/patterns/valid_garment_{id}/gt_image.png`

### 7.4 핵심 기술
- **ChatGarment**: Vision-Language Model 기반 이미지 분석
- **GarmentCode**: 2D 패턴 생성
- **GarmentCodeRC**: 물리 시뮬레이션 기반 3D 변환
- **Agentic AI**: 자동화된 작업 오케스트레이션

---

## 8. 추가 정보

### 8.1 Mock 모드
현재 시스템은 일부 의존성 문제로 인해 **Mock 모드**로 동작할 수 있습니다:
- 실제 모델 로딩 실패 시 Mock 데이터 반환
- 실제 3D 생성 대신 Mock 파일 생성
- 시스템 구조는 정상 작동

### 8.2 성능 최적화
- **모델 로딩**: 지연 로딩 (첫 사용 시에만 로딩)
- **캐싱**: 세션별 메모리 관리
- **병렬 처리**: 향후 구현 예정

### 8.3 확장 가능성
- **렌더링 엔진**: PyTorch3D 통합 예정
- **다양한 의류 타입**: 추가 학습으로 확장 가능
- **실시간 피팅**: 웹 기반 3D 뷰어 통합 예정

---

**작성일**: 2025-01-06  
**버전**: 1.0.0  
**작성자**: ChatGarment 시스템 분석

