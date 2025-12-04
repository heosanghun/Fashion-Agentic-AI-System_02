# Fashion Agentic AI System - 아키텍처 상세 설명

## 📋 목차

1. [전체 시스템 아키텍처](#1-전체-시스템-아키텍처)
2. [각 계층별 상세 설명](#2-각-계층별-상세-설명)
3. [데이터 흐름 상세 분석](#3-데이터-흐름-상세-분석)
4. [컴포넌트 간 상호작용](#4-컴포넌트-간-상호작용)
5. [실행 시퀀스 다이어그램](#5-실행-시퀀스-다이어그램)

---

## 1. 전체 시스템 아키텍처

### 1.1 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 (User)                             │
│                 텍스트 + 이미지 입력                          │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│             Frontend (React + Vite)                          │
│  포트: 5173                                                  │
│  - 파일 업로드                                               │
│  - 텍스트 입력                                               │
│  - 결과 시각화                                               │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ HTTP POST /api/v1/request
┌─────────────────────────────────────────────────────────────┐
│         API Server (FastAPI) - agentic_system/api           │
│  포트: 8000                                                  │
│  - 요청 수신 및 이미지 저장                                   │
│  - Custom UI 호출                                            │
│  - Agent Runtime 호출                                        │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│           Agent Runtime (Agent 1) - 종합 감독                │
│  파일: core/agent_runtime.py                                │
│                                                              │
│  1️⃣ 인식 (Perception)                                       │
│     - 사용자 의도 분석                                        │
│     - 3D 생성 vs 상품 추천 판단                              │
│                                                              │
│  2️⃣ 판단 (Judgment)                                         │
│     - 추상적 작업 계획 수립                                   │
│     - Agent 2에게 전달                                       │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ generate_execution_plan()
┌─────────────────────────────────────────────────────────────┐
│        F.LLM (Agent 2) - 작업 지시 전문가                     │
│  파일: core/f_llm.py                                         │
│  모델: InternVL2-8B (선택적)                                 │
│                                                              │
│  - 추상적 계획 → 구체적 실행 계획 변환                        │
│  - JSON 형식 실행 단계 생성                                  │
│                                                              │
│  예시 실행 계획:                                             │
│  {                                                           │
│    "steps": [                                                │
│      {"step_id": 1, "tool": "extensions_2d_to_3d",          │
│       "action": "analyze_image"},                            │
│      {"step_id": 2, "tool": "extensions_2d_to_3d",          │
│       "action": "generate_pattern"},                         │
│      {"step_id": 3, "tool": "extensions_2d_to_3d",          │
│       "action": "convert_to_3d"},                            │
│      {"step_id": 4, "tool": "extensions_2d_to_3d",          │
│       "action": "render_result"}                             │
│    ]                                                         │
│  }                                                           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ 실행 계획 반환
┌─────────────────────────────────────────────────────────────┐
│        Agent Runtime (Agent 1) - 도구 실행                    │
│                                                              │
│  3️⃣ 행동 (Action)                                           │
│     - 실행 계획의 각 단계를 순차적으로 실행                    │
│     - 등록된 도구 호출                                        │
│     - 의존성 관리 (이전 단계 결과를 다음 단계로 전달)          │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ tools_registry["extensions_2d_to_3d"]()
┌─────────────────────────────────────────────────────────────┐
│      Extensions Tool (2D to 3D) - ChatGarment 통합           │
│  파일: tools/extensions.py                                   │
│  클래스: Extensions2DTo3D                                    │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
         ┌────────────┴────────────┐
         │                         │
    [직접 사용]              [마이크로서비스]
         │                         │
         ↓                         ↓
┌─────────────────┐     ┌──────────────────────┐
│ ChatGarment     │     │ ChatGarment Service  │
│ Pipeline        │     │ (독립 서버)           │
│ (로컬 통합)     │     │ 포트: 9000            │
└─────────────────┘     └──────────────────────┘
         │                         │
         └────────────┬────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              ChatGarment 모델 (LLaVA 기반)                   │
│  파일: tools/chatgarment_integration.py                     │
│  모델: LLaVA-v1.5-7B + ChatGarment 파인튜닝                  │
│                                                              │
│  단계 1: 이미지 분석 (Geometry Features)                     │
│  단계 2: 패턴 코드 생성 (Sewing Pattern Code)                │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│            GarmentCodeRC (2D → 3D 변환)                      │
│  파일: ChatGarment/llava/garment_utils_v2.py                │
│                                                              │
│  - 패턴 JSON 생성                                            │
│  - 물리 시뮬레이션                                            │
│  - 3D 메시 생성 (.obj 파일)                                  │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                   결과 반환                                  │
│                                                              │
│  {                                                           │
│    "status": "success",                                      │
│    "analysis": {...},           # 이미지 분석 결과           │
│    "pattern_path": "...",       # 패턴 JSON 경로             │
│    "mesh_path": "...",          # 3D 메시 파일 경로          │
│    "render_path": "..."         # 렌더링 이미지 경로         │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 각 계층별 상세 설명

### 2.1 사용자 인터페이스 계층

#### Frontend (React + Vite)

**위치**: `agentic_system/frontend/`

**기술 스택**:
- React 18.2.0
- Vite 5.0.0
- Three.js 0.158.0 (3D 뷰어)
- Axios 1.6.0 (HTTP 클라이언트)

**주요 컴포넌트**:

1. **App.jsx** - 메인 애플리케이션
   - 상태 관리 (이미지, 텍스트, 로딩, 결과)
   - API 호출 처리
   - 에러 처리

2. **ImageUpload.jsx** - 이미지 업로드
   - 드래그 앤 드롭 지원
   - 파일 선택
   - 이미지 미리보기

3. **StatusBar.jsx** - 상태 표시
   - 로딩 상태
   - 처리 진행 상황

4. **ResultViewer.jsx** - 결과 표시
   - 분석 결과 표시
   - 패턴 정보 표시
   - 이미지 갤러리

5. **ModelViewer.jsx** - 3D 모델 뷰어
   - Three.js 기반 3D 렌더링
   - 인터랙티브 조작 (회전, 확대/축소)

**데이터 흐름**:
```javascript
// 사용자 입력
const formData = new FormData();
formData.append('text', textInput);
formData.append('image', imageFile);
formData.append('session_id', sessionId);

// API 호출
const response = await axios.post(
  'http://localhost:8000/api/v1/request',
  formData,
  { headers: { 'Content-Type': 'multipart/form-data' } }
);

// 결과 처리
setResult(response.data);
```

---

### 2.2 API 서버 계층

#### FastAPI Server

**위치**: `agentic_system/api/main.py`

**포트**: 8000

**주요 기능**:

1. **요청 수신 및 검증**
   ```python
   @app.post("/api/v1/request")
   async def process_request(
       text: Optional[str] = Form(None),
       image: Optional[UploadFile] = File(None),
       session_id: Optional[str] = Form(None)
   ):
   ```

2. **이미지 저장**
   ```python
   upload_dir = project_root / "uploads"
   image_path = upload_dir / f"{session_id}_{image.filename}"
   with open(image_path, "wb") as f:
       f.write(await image.read())
   ```

3. **Custom UI 호출**
   ```python
   payload = custom_ui.process_user_input(
       text=text,
       image_path=image_path,
       session_id=session_id
   )
   ```

4. **Agent Runtime 호출**
   ```python
   result = agent_runtime.process_request(
       payload.dict(),
       session_id=session_id
   )
   ```

5. **결과 반환**
   ```python
   response = custom_ui.format_output(result)
   return JSONResponse(content=response)
   ```

**CORS 설정**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 2.3 Agentic AI 프레임워크 계층

#### Agent Runtime (Agent 1)

**위치**: `agentic_system/core/agent_runtime.py`

**역할**: 종합 감독 에이전트

**3단계 프로세스**:

##### 1️⃣ 인식 (Perception)

```python
def _analyze_user_intent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    input_data = payload.get("input_data", {})
    text = input_data.get("text", "").lower()
    has_image = input_data.get("has_image", False)
    
    # 의도 추론
    if "입혀줘" in text or "가상 피팅" in text or has_image:
        intent_type = "3d_generation"
    elif "추천" in text or "찾아줘" in text:
        intent_type = "garment_recommendation"
    else:
        intent_type = "3d_generation"  # 기본값
    
    return {
        "type": intent_type,
        "confidence": 0.9,
        "text": text,
        "has_image": has_image
    }
```

**출력**: 사용자 의도 정보
- `type`: "3d_generation" 또는 "garment_recommendation"
- `confidence`: 신뢰도 (0.0 ~ 1.0)
- `text`: 원본 텍스트
- `has_image`: 이미지 존재 여부

##### 2️⃣ 판단 (Judgment)

```python
def _create_abstract_plan(
    self,
    user_intent: Dict[str, Any],
    payload: Dict[str, Any],
    memory: ShortTermMemory
) -> AbstractPlan:
    intent_type = user_intent["type"]
    
    if intent_type == "3d_generation":
        return AbstractPlan(
            plan_type="3d_generation",
            goal="2D 이미지를 3D 가상 피팅으로 변환",
            steps=[
                "의류 이미지 분석",
                "3D 패턴 생성",
                "3D 모델 변환",
                "렌더링 및 시각화"
            ],
            parameters={
                "image_path": payload.get("input_data", {}).get("image_path"),
                "text": payload.get("input_data", {}).get("text")
            },
            created_at=datetime.now().isoformat()
        )
```

**출력**: 추상적 작업 계획
- `plan_type`: 계획 유형
- `goal`: 목표 설명
- `steps`: 추상적 단계 목록
- `parameters`: 필요한 파라미터

**Agent 2 호출**:
```python
execution_plan = self.agent2.generate_execution_plan(
    abstract_plan.dict(),
    context=input_data,
    rag_context=None,
    user_text=input_data.get("text"),
    image_path=input_data.get("image_path")
)
```

##### 3️⃣ 행동 (Action)

```python
def _execute_plan(
    self,
    execution_plan: ExecutionPlan,
    memory: ShortTermMemory
) -> Dict[str, Any]:
    results = {}
    execution_context = {}
    
    # 단계별 실행 (의존성 고려)
    for step in execution_plan.steps:
        step_id = step["step_id"]
        tool_name = step["tool"]
        action = step["action"]
        parameters = step.get("parameters", {})
        dependencies = step.get("dependencies", [])
        
        # 의존성 확인
        if dependencies:
            for dep_id in dependencies:
                if dep_id in results:
                    parameters["_dependency_result"] = results[dep_id]["result"]
        
        # 도구 실행
        tool_func = self.tools_registry[tool_name]
        step_result = tool_func(action, parameters, execution_context)
        
        # 결과 저장
        results[step_id] = {
            "status": "success",
            "result": step_result,
            "step_id": step_id
        }
        execution_context[f"step_{step_id}"] = step_result
    
    return {"status": "completed", "steps": results}
```

**의존성 관리**:
- 각 단계는 `dependencies` 리스트를 통해 이전 단계를 참조
- 이전 단계의 결과는 `_dependency_result` 파라미터로 전달
- 실행 컨텍스트에 중간 결과 저장

**자기 수정 루프**:
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

---

#### F.LLM (Agent 2)

**위치**: `agentic_system/core/f_llm.py`

**역할**: 작업 지시 전문가 에이전트

**주요 기능**:

1. **추상적 계획을 구체적 실행 계획으로 변환**

```python
def generate_execution_plan(
    self,
    abstract_plan: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    rag_context: Optional[Dict[str, Any]] = None,
    user_text: Optional[str] = None,
    image_path: Optional[str] = None
) -> ExecutionPlan:
    # LLM 기반 계획 생성 (선택적)
    if use_llm and self.llm_model:
        enhanced_plan = self._generate_plan_with_llm(...)
    else:
        enhanced_plan = abstract_plan  # 규칙 기반
    
    # 실행 단계 생성
    steps = self._create_execution_steps(enhanced_plan, context)
    
    return ExecutionPlan(
        plan_id=f"plan_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        steps=steps,
        tools_required=self._extract_required_tools(steps),
        parameters=self._extract_parameters(enhanced_plan),
        estimated_time=self._estimate_execution_time(steps),
        created_at=datetime.now().isoformat()
    )
```

2. **실행 단계 생성**

```python
def _create_3d_generation_steps(
    self, 
    plan: Dict[str, Any], 
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    steps = [
        {
            "step_id": 1,
            "tool": "extensions_2d_to_3d",
            "action": "analyze_image",
            "parameters": {
                "image_path": context.get("image_path"),
                "text_description": context.get("text")
            },
            "dependencies": []
        },
        {
            "step_id": 2,
            "tool": "extensions_2d_to_3d",
            "action": "generate_pattern",
            "parameters": {},
            "dependencies": [1]  # 단계 1의 결과 필요
        },
        {
            "step_id": 3,
            "tool": "extensions_2d_to_3d",
            "action": "convert_to_3d",
            "parameters": {},
            "dependencies": [2]  # 단계 2의 결과 필요
        },
        {
            "step_id": 4,
            "tool": "extensions_2d_to_3d",
            "action": "render_result",
            "parameters": {},
            "dependencies": [3]  # 단계 3의 결과 필요
        }
    ]
    return steps
```

**InternVL2 통합** (선택적):
- 현재 PoC 단계에서는 성능 최적화를 위해 비활성화
- 향후 Pilot 단계에서 활성화 예정
- LLM을 사용하면 더 지능적인 실행 계획 생성 가능

---

### 2.4 도구 시스템 계층

#### Extensions Tool (2D→3D 변환)

**위치**: `agentic_system/tools/extensions.py`

**클래스**: `Extensions2DTo3D`

**주요 액션**:

##### 1. analyze_image

```python
def _analyze_image(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    image_path = parameters.get("image_path")
    
    # ChatGarment Pipeline 사용
    if self.chatgarment_pipeline:
        result = self.chatgarment_pipeline.analyze_image(image_path)
        return {
            "status": "success",
            "analysis": result.get("analysis", {}),
            "text_output": result.get("text_output", ""),
            "float_preds": result.get("float_preds"),
            "image_path": image_path
        }
```

**출력**:
```json
{
  "status": "success",
  "analysis": {
    "upper_garment": ["T-shirt", "short sleeves"],
    "lower_garment": []
  },
  "text_output": "...",
  "float_preds": [...],
  "image_path": "/path/to/image.jpg"
}
```

##### 2. generate_pattern

```python
def _generate_pattern(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # 이전 단계 결과 사용
    analysis = parameters.get("_dependency_result") or context.get("step_1")
    json_output = analysis.get("analysis")
    float_preds = analysis.get("float_preds")
    
    # GarmentCode 패턴 생성
    all_json_spec_files = run_garmentcode_parser_float50(
        all_json_spec_files,
        json_output,
        float_preds,
        saved_dir
    )
    
    return {
        "status": "success",
        "pattern_path": pattern_json_path,
        "pattern_info": {...}
    }
```

##### 3. convert_to_3d

```python
def _convert_to_3d(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # 이전 단계 결과 사용
    pattern_result = parameters.get("_dependency_result") or context.get("step_2")
    pattern_json_path = pattern_result.get("pattern_path")
    
    # GarmentCodeRC 시뮬레이션 실행
    sim_script = project_root / "ChatGarment" / "run_garmentcode_sim.py"
    result = subprocess.run(
        f'python "{sim_script}" --json_spec_file "{pattern_json_path}"',
        shell=True,
        timeout=600
    )
    
    return {
        "status": "success",
        "mesh_path": mesh_path,
        "mesh_info": {...}
    }
```

##### 4. render_result

```python
def _render_result(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    mesh_result = parameters.get("_dependency_result") or context.get("step_3")
    mesh_path = mesh_result.get("mesh_path")
    
    # 렌더링 (현재는 Mock)
    render_path = self._mock_render(mesh_result)
    
    return {
        "status": "success",
        "render_path": render_path,
        "visualization": {
            "image_path": render_path,
            "mesh_path": mesh_path
        }
    }
```

---

#### ChatGarment Pipeline

**위치**: `agentic_system/tools/chatgarment_integration.py`

**클래스**: `ChatGarmentPipeline`

**주요 메서드**:

##### 1. load_model()

```python
def load_model(self):
    # 모델 인자 설정
    model_args = ModelArguments(model_name_or_path=self.model_path)
    data_args = DataArguments(image_aspect_ratio="pad")
    
    # 토크나이저 로딩
    self.tokenizer = transformers.AutoTokenizer.from_pretrained(...)
    
    # 모델 생성
    self.model = GarmentGPTFloat50ForCausalLM.from_pretrained(
        self.model_path,
        torch_dtype=torch.bfloat16,
        seg_token_idx=seg_token_idx
    )
    
    # 체크포인트 로딩
    state_dict = torch.load(self.checkpoint_path, map_location="cpu")
    self.model.load_state_dict(state_dict, strict=False)
    
    # 디바이스 설정
    self.model = self.model.bfloat16().cuda().eval()
    
    self.model_loaded = True
```

##### 2. analyze_image()

```python
def analyze_image(self, image_path: str) -> Dict[str, Any]:
    # 이미지 로딩 및 전처리
    image = Image.open(image_path).convert('RGB')
    image_clip = self.image_processor.preprocess(image)
    image_clip = image_clip.to(self.device).bfloat16()
    
    # 프롬프트 구성
    question = 'Can you describe the geometry features of the garments?'
    prompt = DEFAULT_IMAGE_TOKEN + "\n" + question
    
    # 모델 추론
    with torch.no_grad():
        output_ids, _, _ = self.model.evaluate(
            image_clip, image_clip, input_ids,
            max_new_tokens=2048,
            tokenizer=self.tokenizer
        )
    
    # 결과 파싱
    text_output = self.tokenizer.decode(output_ids)
    json_output = repair_json(text_output)
    
    return {
        "status": "success",
        "analysis": json_output,
        "text_output": text_output
    }
```

---

### 2.5 AI 모델 및 라이브러리 계층

#### ChatGarment 모델 (LLaVA 기반)

**모델**: LLaVA-v1.5-7B + ChatGarment 파인튜닝

**체크포인트**: `checkpoints/try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final/pytorch_model.bin`

**주요 기능**:
- 이미지에서 의류의 기하학적 특징 추출
- 재봉 패턴 코드 생성
- Float 예측값 생성 (GarmentCode 파라미터)

#### GarmentCodeRC

**역할**: 2D 패턴을 3D 메시로 변환

**주요 기능**:
- JSON 패턴 사양 파싱
- 물리 시뮬레이션 (의류 드레이핑)
- 3D 메시 생성 (.obj 파일)

---

## 3. 데이터 흐름 상세 분석

### 3.1 전체 데이터 흐름

```
[1] 사용자 입력
    ├─ 텍스트: "이 옷을 입혀줘"
    └─ 이미지: TShirt.jpg
        ↓
[2] Frontend (App.jsx)
    ├─ FormData 생성
    ├─ session_id 생성
    └─ HTTP POST 요청
        ↓
[3] API Server (main.py)
    ├─ 이미지 저장: uploads/session_12345_TShirt.jpg
    ├─ Custom UI 호출
    └─ JSONPayload 생성
        ↓
[4] Agent Runtime (Agent 1)
    ├─ [인식] _analyze_user_intent()
    │   └─ 결과: {"type": "3d_generation", "confidence": 0.9}
    ├─ [판단] _create_abstract_plan()
    │   └─ 결과: AbstractPlan
    └─ Agent 2 호출
        ↓
[5] F.LLM (Agent 2)
    ├─ generate_execution_plan()
    ├─ _create_execution_steps()
    └─ ExecutionPlan 반환
        ↓
[6] Agent Runtime (Agent 1)
    ├─ [행동] _execute_plan()
    ├─ 단계별 도구 실행
    └─ 의존성 관리
        ↓
[7] Extensions Tool
    ├─ Step 1: analyze_image()
    │   └─ ChatGarment Pipeline 호출
    ├─ Step 2: generate_pattern()
    │   └─ GarmentCode 패턴 생성
    ├─ Step 3: convert_to_3d()
    │   └─ GarmentCodeRC 시뮬레이션
    └─ Step 4: render_result()
        └─ 렌더링 이미지 생성
        ↓
[8] 결과 반환
    ├─ API Server
    ├─ Frontend
    └─ 사용자에게 표시
```

### 3.2 단계별 데이터 변환

#### Step 1: 이미지 분석

**입력**: 이미지 파일 (JPG/PNG)
**처리**: ChatGarment 모델 추론
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
**처리**: GarmentCode 파서 실행
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
**처리**: 렌더링 엔진 (현재 Mock)
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

## 4. 컴포넌트 간 상호작용

### 4.1 Agent 1 ↔ Agent 2

```
Agent 1 (Agent Runtime)
    │
    ├─ generate_execution_plan() 호출
    │   ├─ abstract_plan 전달
    │   ├─ context 전달
    │   ├─ user_text 전달
    │   └─ image_path 전달
    │
    └─ ExecutionPlan 수신
        ├─ plan_id
        ├─ steps (실행 단계 목록)
        ├─ tools_required
        └─ estimated_time
```

### 4.2 Agent Runtime ↔ Tools

```
Agent Runtime
    │
    ├─ tools_registry 조회
    │   └─ tool_func = tools_registry[tool_name]
    │
    ├─ tool_func() 호출
    │   ├─ action: "analyze_image"
    │   ├─ parameters: {...}
    │   └─ context: {...}
    │
    └─ step_result 수신
        ├─ status: "success"
        └─ result: {...}
```

### 4.3 Extensions Tool ↔ ChatGarment Pipeline

```
Extensions Tool
    │
    ├─ chatgarment_pipeline.analyze_image() 호출
    │   └─ image_path 전달
    │
    └─ result 수신
        ├─ analysis: {...}
        ├─ text_output: "..."
        └─ float_preds: [...]
```

---

## 5. 실행 시퀀스 다이어그램

### 5.1 전체 실행 시퀀스

```
User          Frontend        API Server      Agent 1        Agent 2        Extensions      ChatGarment
 │                │                │              │              │              │                │
 │──텍스트+이미지──>│                │              │              │              │                │
 │                │──HTTP POST──>│                │              │              │                │
 │                │                │──이미지 저장─>│              │              │                │
 │                │                │──Custom UI──>│              │              │                │
 │                │                │              │──JSONPayload─>│              │                │
 │                │                │              │              │              │                │
 │                │                │              │──인식(Perception)─────────────│              │
 │                │                │              │              │              │                │
 │                │                │              │──판단(Judgment)───────────────│              │
 │                │                │              │──AbstractPlan──────────────>│              │                │
 │                │                │              │              │──ExecutionPlan 생성─────────│              │
 │                │                │              │<─ExecutionPlan───────────────│              │                │
 │                │                │              │              │              │                │
 │                │                │              │──행동(Action)─────────────────────────────────│              │
 │                │                │              │──extensions_2d_to_3d─────────>│              │
 │                │                │              │              │              │──analyze_image─>│
 │                │                │              │              │              │<─result─────────│
 │                │                │              │              │              │──generate_pattern─>│
 │                │                │              │              │              │<─result─────────│
 │                │                │              │              │              │──convert_to_3d─>│
 │                │                │              │              │              │<─result─────────│
 │                │                │              │              │              │──render_result─>│
 │                │                │              │              │              │<─result─────────│
 │                │                │              │<─final_result───────────────────────────────────│
 │                │                │<─JSONResponse─────────────────────────────────────────────────│
 │                │<─response───────────────────────────────────────────────────────────────────────│
 │<─결과 표시───────────────────────────────────────────────────────────────────────────────────────│
```

### 5.2 의존성 기반 실행

```
Step 1: analyze_image
    │
    └─> 결과: analysis_result
            │
            └─> Step 2: generate_pattern
                    │ (의존성: analysis_result)
                    │
                    └─> 결과: pattern_result
                            │
                            └─> Step 3: convert_to_3d
                                    │ (의존성: pattern_result)
                                    │
                                    └─> 결과: mesh_result
                                            │
                                            └─> Step 4: render_result
                                                    │ (의존성: mesh_result)
                                                    │
                                                    └─> 최종 결과
```

---

## 6. 결론

본 아키텍처는 다음과 같은 특징을 가진다:

1. **계층화된 구조**: 각 계층이 명확한 역할을 담당
2. **확장 가능성**: 새로운 도구를 쉽게 추가 가능
3. **의존성 관리**: 단계 간 의존성을 자동으로 관리
4. **자기 수정 루프**: 실패 시 자동 재시도
5. **멀티모달 처리**: 텍스트와 이미지를 동시에 처리

이러한 구조를 통해 복잡한 의류 생성 작업을 자율적으로 수행할 수 있는 지능형 시스템을 구현하였다.

