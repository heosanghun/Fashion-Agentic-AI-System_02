# 다이어그램 파일명 ↔ 실제 코드베이스 파일 매핑

## 📋 목차

1. [파일명 매핑 테이블](#1-파일명-매핑-테이블)
2. [각 컴포넌트별 상세 위치 정보](#2-각-컴포넌트별-상세-위치-정보)
3. [주요 함수/메서드 위치](#3-주요-함수메서드-위치)
4. [코드 수정 가이드](#4-코드-수정-가이드)

---

## 1. 파일명 매핑 테이블

| 다이어그램 파일명 | 실제 파일 경로 | 상태 |
|------------------|---------------|------|
| `core_agent_runtime.py` | `agentic_system/core/agent_runtime.py` | ✅ 정확 |
| `core_llm.py` | `agentic_system/core/f_llm.py` | ⚠️ 파일명 다름 |
| `tools/extensions.py` | `agentic_system/tools/extensions.py` | ✅ 정확 |
| `tools/chatgarment_integraion.py` | `agentic_system/tools/chatgarment_integration.py` | ⚠️ 오타 수정 필요 |
| `ChatGarment_llava_utile_v2.py` | `ChatGarment/llava/garment_utils_v2.py` | ⚠️ 경로 및 파일명 다름 |

---

## 2. 각 컴포넌트별 상세 위치 정보

### 2.1 Agent Runtime (Agent 1) - 종합 감독

#### 파일 위치
- **다이어그램**: `core_agent_runtime.py`
- **실제 경로**: `agentic_system/core/agent_runtime.py`

#### 클래스 정의
```python
# 파일: agentic_system/core/agent_runtime.py
# 라인: 30
class AgentRuntime:
    """Agent Runtime - Agent 1 (종합 감독 에이전트)"""
```

#### 주요 메서드 위치

##### 1. 인식 (Perception) - 사용자 의도 분석
```python
# 파일: agentic_system/core/agent_runtime.py
# 라인: 105-129
def _analyze_user_intent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 의도 분석
    - 3D 생성 vs 상품 추천 판단
    """
```

**핵심 로직**:
- 라인 117-122: 의도 유형 판단 로직
- 라인 124-129: 결과 반환

##### 2. 판단 (Judgment) - 추상적 작업 계획 수립
```python
# 파일: agentic_system/core/agent_runtime.py
# 라인: 131-174
def _create_abstract_plan(
    self,
    user_intent: Dict[str, Any],
    payload: Dict[str, Any],
    memory: ShortTermMemory
) -> AbstractPlan:
    """
    추상적 작업 계획 수립
    - Agent 2에게 전달
    """
```

**핵심 로직**:
- 라인 144-159: 3D 생성 계획 생성
- 라인 160-174: 상품 추천 계획 생성

##### 3. 행동 (Action) - 실행 계획 실행
```python
# 파일: agentic_system/core/agent_runtime.py
# 라인: 176-253
def _execute_plan(
    self,
    execution_plan: ExecutionPlan,
    memory: ShortTermMemory
) -> Dict[str, Any]:
    """
    실행 계획의 각 단계를 순차적으로 실행
    - 등록된 도구 호출
    - 의존성 관리
    """
```

**핵심 로직**:
- 라인 191-197: 단계별 실행 루프
- 라인 200-210: 의존성 확인 및 파라미터 추가
- 라인 213-235: 도구 실행 및 결과 저장

##### 4. 메인 요청 처리
```python
# 파일: agentic_system/core/agent_runtime.py
# 라인: 53-103
def process_request(
    self,
    payload: Dict[str, Any],
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    사용자 요청 처리
    - 전체 프로세스 오케스트레이션
    """
```

**핵심 로직**:
- 라인 71: 인식 단계 호출
- 라인 74: 판단 단계 호출
- 라인 78-84: Agent 2 호출
- 라인 87: 행동 단계 호출
- 라인 90-94: 자기 수정 루프

---

### 2.2 F.LLM (Agent 2) - 작업 지시 전문가

#### 파일 위치
- **다이어그램**: `core_llm.py`
- **실제 경로**: `agentic_system/core/f_llm.py` ⚠️ **파일명 다름**

#### 클래스 정의
```python
# 파일: agentic_system/core/f_llm.py
# 라인: 39
class FLLM:
    """Foundation LLM (F.LLM) - Agent 2"""
```

#### 주요 메서드 위치

##### 1. 실행 계획 생성 (메인 함수)
```python
# 파일: agentic_system/core/f_llm.py
# 라인: 86-143
def generate_execution_plan(
    self,
    abstract_plan: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    rag_context: Optional[Dict[str, Any]] = None,
    user_text: Optional[str] = None,
    image_path: Optional[str] = None
) -> ExecutionPlan:
    """
    추상적 계획을 구체적인 실행 계획으로 변환
    - JSON 형식 실행 단계 생성
    """
```

**핵심 로직**:
- 라인 113-118: LLM 기반 계획 생성 (선택적)
- 라인 120-122: 규칙 기반 계획 생성 (기본값)
- 라인 126: 실행 단계 생성
- 라인 133-140: ExecutionPlan 객체 생성

##### 2. 실행 단계 생성
```python
# 파일: agentic_system/core/f_llm.py
# 라인: 293-340
def _create_execution_steps(
    self, 
    plan: Dict[str, Any], 
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    실행 단계 생성
    - 계획 유형에 따라 다른 단계 생성
    """
```

**핵심 로직**:
- 라인 320-322: 3D 생성 단계 생성
- 라인 323-325: 상품 추천 단계 생성

##### 3. 3D 생성 단계 생성
```python
# 파일: agentic_system/core/f_llm.py
# 라인: 342-381
def _create_3d_generation_steps(
    self, 
    plan: Dict[str, Any], 
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    3D 생성 경로의 실행 단계 생성
    - 4단계: analyze_image → generate_pattern → convert_to_3d → render_result
    """
```

**핵심 로직**:
- 라인 348-358: Step 1 - analyze_image
- 라인 359-365: Step 2 - generate_pattern (의존성: [1])
- 라인 366-372: Step 3 - convert_to_3d (의존성: [2])
- 라인 373-379: Step 4 - render_result (의존성: [3])

---

### 2.3 Extension Tool - ChatGarment 통합

#### 파일 위치
- **다이어그램**: `tools/extensions.py`
- **실제 경로**: `agentic_system/tools/extensions.py` ✅ **정확**

#### 클래스 정의
```python
# 파일: agentic_system/tools/extensions.py
# 라인: 58
class Extensions2DTo3D:
    """Extensions Tool - 2D to 3D 변환"""
```

#### 주요 메서드 위치

##### 1. 도구 실행 메인 함수
```python
# 파일: agentic_system/tools/extensions.py
# 라인: 263-309
def execute(self, action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    도구 실행
    - action에 따라 적절한 메서드 호출
    """
```

**핵심 로직**:
- 라인 278-282: analyze_image 액션
- 라인 283-287: generate_pattern 액션
- 라인 288-292: convert_to_3d 액션
- 라인 293-297: render_result 액션

##### 2. 이미지 분석
```python
# 파일: agentic_system/tools/extensions.py
# 라인: 311-473
def _analyze_image(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    이미지 분석 (ChatGarment 모델 사용)
    """
```

**핵심 로직**:
- 라인 327: 모델 로딩
- 라인 335-353: ChatGarmentPipeline 사용 (권장)
- 라인 360-469: 직접 모델 사용 (Fallback)

##### 3. 패턴 생성
```python
# 파일: agentic_system/tools/extensions.py
# 라인: 475-528
def _generate_pattern(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    패턴 생성 (GarmentCode 사용)
    """
```

**핵심 로직**:
- 라인 482-485: 이전 단계 결과 사용
- 라인 501-506: GarmentCode 파서 실행

##### 4. 3D 변환
```python
# 파일: agentic_system/tools/extensions.py
# 라인: 530-602
def _convert_to_3d(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    3D 모델로 변환 (GarmentCodeRC 사용)
    """
```

**핵심 로직**:
- 라인 537-541: 이전 단계 결과 사용
- 라인 559-598: 실제 3D 변환 시도 (선택적)
- 라인 601-602: Mock 변환 (기본값)

##### 5. 렌더링
```python
# 파일: agentic_system/tools/extensions.py
# 라인: 604-628
def _render_result(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    결과 렌더링
    """
```

---

### 2.4 ChatGarment 모델 (LLaVA 기반)

#### 파일 위치
- **다이어그램**: `tools/chatgarment_integraion.py` ⚠️ **오타**
- **실제 경로**: `agentic_system/tools/chatgarment_integration.py` ✅ **정확한 파일명**

#### 클래스 정의
```python
# 파일: agentic_system/tools/chatgarment_integration.py
# 라인: 102
class ChatGarmentPipeline:
    """ChatGarment 완전한 파이프라인"""
```

#### 주요 메서드 위치

##### 1. 모델 로딩
```python
# 파일: agentic_system/tools/chatgarment_integration.py
# 라인: 142-268
def load_model(self):
    """ChatGarment 모델 로딩"""
```

**핵심 로직**:
- 라인 184-193: 토크나이저 로딩
- 라인 196-201: 모델 생성
- 라인 230-239: 체크포인트 로딩
- 라인 245-248: 디바이스 설정

##### 2. Step 1: 이미지 분석 (Geometry Features)
```python
# 파일: agentic_system/tools/chatgarment_integration.py
# 라인: 270-362
def analyze_image(self, image_path: str) -> Dict[str, Any]:
    """
    이미지 분석만 수행 (Geometry features 추출)
    """
```

**핵심 로직**:
- 라인 290-311: 이미지 로딩 및 전처리
- 라인 314-315: 프롬프트 구성
- 라인 327-334: 모델 추론
- 라인 336-344: 결과 파싱

**프롬프트**:
```python
# 라인: 315
question = 'Can you describe the geometry features of the garments worn by the model in the Json format?'
```

##### 3. Step 2: 패턴 코드 생성 (Sewing Pattern Code)
```python
# 파일: agentic_system/tools/chatgarment_integration.py
# 라인: 364-608
def process_image_to_garment(
    self,
    image_path: str,
    output_dir: Optional[str] = None,
    garment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    이미지를 처리하여 3D 의류 생성
    - 전체 파이프라인: Step 1 + Step 2
    """
```

**핵심 로직**:
- 라인 437-468: Step 1 - Geometry Features 추출
- 라인 479-513: Step 2 - Sewing Pattern Code 생성
- 라인 545-551: GarmentCode 패턴 생성

**Step 2 프롬프트**:
```python
# 라인: 481
question2 = 'Can you estimate the sewing pattern code based on the image and Json format garment geometry description?'
```

---

### 2.5 GarmentCodeRC (2D→3D 변환)

#### 파일 위치
- **다이어그램**: `ChatGarment_llava_utile_v2.py` ⚠️ **경로 및 파일명 다름**
- **실제 경로**: `ChatGarment/llava/garment_utils_v2.py` ✅ **정확한 경로**

#### 주요 함수 위치

##### 1. GarmentCode 파서 실행
```python
# 파일: ChatGarment/llava/garment_utils_v2.py
# 라인: 353-391
def run_garmentcode_parser_float50(all_json_spec_files, json_output, float_preds, output_dir):
    """
    GarmentCode 패턴 생성
    - JSON 출력 + Float 예측값 → 패턴 JSON 파일
    """
```

**핵심 로직**:
- 라인 354-368: 상하의 분리 처리
- 라인 377-389: 원피스 처리
- 라인 367, 385: `try_generate_garments()` 호출

##### 2. 3D 시뮬레이션 실행 스크립트
```python
# 파일: ChatGarment/run_garmentcode_sim.py
# (전체 파일)
```

**사용 위치**:
- `agentic_system/tools/chatgarment_integration.py` 라인 610-699
- `agentic_system/tools/extensions.py` 라인 554-598

**호출 코드 예시**:
```python
# agentic_system/tools/chatgarment_integration.py
# 라인: 629-666
sim_script = chatgarment_path / "run_garmentcode_sim.py"
subprocess.run([
    sys.executable,
    str(sim_script),
    "--json_spec_file", json_spec_path_abs
], cwd=str(project_root), timeout=600)
```

---

## 3. 주요 함수/메서드 위치

### 3.1 Agent Runtime (Agent 1) 메서드

| 메서드명 | 파일 경로 | 라인 번호 | 설명 |
|---------|----------|----------|------|
| `process_request()` | `agentic_system/core/agent_runtime.py` | 53-103 | 메인 요청 처리 |
| `_analyze_user_intent()` | `agentic_system/core/agent_runtime.py` | 105-129 | 인식: 사용자 의도 분석 |
| `_create_abstract_plan()` | `agentic_system/core/agent_runtime.py` | 131-174 | 판단: 추상적 계획 수립 |
| `_execute_plan()` | `agentic_system/core/agent_runtime.py` | 176-253 | 행동: 실행 계획 실행 |
| `_self_correction_loop()` | `agentic_system/core/agent_runtime.py` | 255-295 | 자기 수정 루프 |

### 3.2 F.LLM (Agent 2) 메서드

| 메서드명 | 파일 경로 | 라인 번호 | 설명 |
|---------|----------|----------|------|
| `generate_execution_plan()` | `agentic_system/core/f_llm.py` | 86-143 | 실행 계획 생성 (메인) |
| `_create_execution_steps()` | `agentic_system/core/f_llm.py` | 293-340 | 실행 단계 생성 |
| `_create_3d_generation_steps()` | `agentic_system/core/f_llm.py` | 342-381 | 3D 생성 단계 생성 |
| `_create_recommendation_steps()` | `agentic_system/core/f_llm.py` | 383-408 | 상품 추천 단계 생성 |

### 3.3 Extension Tool 메서드

| 메서드명 | 파일 경로 | 라인 번호 | 설명 |
|---------|----------|----------|------|
| `execute()` | `agentic_system/tools/extensions.py` | 263-309 | 도구 실행 메인 함수 |
| `_analyze_image()` | `agentic_system/tools/extensions.py` | 311-473 | 이미지 분석 |
| `_generate_pattern()` | `agentic_system/tools/extensions.py` | 475-528 | 패턴 생성 |
| `_convert_to_3d()` | `agentic_system/tools/extensions.py` | 530-602 | 3D 변환 |
| `_render_result()` | `agentic_system/tools/extensions.py` | 604-628 | 렌더링 |

### 3.4 ChatGarment Pipeline 메서드

| 메서드명 | 파일 경로 | 라인 번호 | 설명 |
|---------|----------|----------|------|
| `load_model()` | `agentic_system/tools/chatgarment_integration.py` | 142-268 | 모델 로딩 |
| `analyze_image()` | `agentic_system/tools/chatgarment_integration.py` | 270-362 | Step 1: 이미지 분석 |
| `process_image_to_garment()` | `agentic_system/tools/chatgarment_integration.py` | 364-608 | 전체 파이프라인 |

### 3.5 GarmentCodeRC 함수

| 함수명 | 파일 경로 | 라인 번호 | 설명 |
|--------|----------|----------|------|
| `run_garmentcode_parser_float50()` | `ChatGarment/llava/garment_utils_v2.py` | 353-391 | 패턴 JSON 생성 |
| `run_garmentcode_sim.py` | `ChatGarment/run_garmentcode_sim.py` | 전체 | 3D 시뮬레이션 실행 |

---

## 4. 코드 수정 가이드

### 4.1 다이어그램 파일명 수정 권장사항

다이어그램을 실제 코드베이스와 일치시키려면 다음 수정이 필요합니다:

#### 1. Agent Runtime 파일명
- **현재 다이어그램**: `core_agent_runtime.py`
- **실제 파일**: `agentic_system/core/agent_runtime.py`
- **권장 수정**: `core/agent_runtime.py` 또는 전체 경로 표시

#### 2. F.LLM 파일명
- **현재 다이어그램**: `core_llm.py`
- **실제 파일**: `agentic_system/core/f_llm.py`
- **권장 수정**: `core/f_llm.py` (파일명이 `f_llm.py`임)

#### 3. ChatGarment Integration 파일명
- **현재 다이어그램**: `tools/chatgarment_integraion.py` (오타)
- **실제 파일**: `agentic_system/tools/chatgarment_integration.py`
- **권장 수정**: `tools/chatgarment_integration.py` (오타 수정)

#### 4. GarmentCodeRC 파일명
- **현재 다이어그램**: `ChatGarment_llava_utile_v2.py`
- **실제 파일**: `ChatGarment/llava/garment_utils_v2.py`
- **권장 수정**: `ChatGarment/llava/garment_utils_v2.py` (전체 경로)

### 4.2 주요 수정 포인트 체크리스트

#### Agent Runtime (Agent 1)
- [x] 파일 경로: `agentic_system/core/agent_runtime.py`
- [x] 클래스명: `AgentRuntime`
- [x] 인식 메서드: `_analyze_user_intent()` (라인 105)
- [x] 판단 메서드: `_create_abstract_plan()` (라인 131)
- [x] 행동 메서드: `_execute_plan()` (라인 176)

#### F.LLM (Agent 2)
- [x] 파일 경로: `agentic_system/core/f_llm.py` ⚠️ **파일명 주의**
- [x] 클래스명: `FLLM`
- [x] 실행 계획 생성: `generate_execution_plan()` (라인 86)
- [x] 실행 단계 생성: `_create_execution_steps()` (라인 293)
- [x] 3D 생성 단계: `_create_3d_generation_steps()` (라인 342)

#### Extension Tool
- [x] 파일 경로: `agentic_system/tools/extensions.py`
- [x] 클래스명: `Extensions2DTo3D`
- [x] 실행 메서드: `execute()` (라인 263)
- [x] 이미지 분석: `_analyze_image()` (라인 311)
- [x] 패턴 생성: `_generate_pattern()` (라인 475)
- [x] 3D 변환: `_convert_to_3d()` (라인 530)
- [x] 렌더링: `_render_result()` (라인 604)

#### ChatGarment Pipeline
- [x] 파일 경로: `agentic_system/tools/chatgarment_integration.py` ⚠️ **오타 수정**
- [x] 클래스명: `ChatGarmentPipeline`
- [x] 모델 로딩: `load_model()` (라인 142)
- [x] Step 1 분석: `analyze_image()` (라인 270)
- [x] 전체 파이프라인: `process_image_to_garment()` (라인 364)

#### GarmentCodeRC
- [x] 파일 경로: `ChatGarment/llava/garment_utils_v2.py` ⚠️ **경로 주의**
- [x] 패턴 생성 함수: `run_garmentcode_parser_float50()` (라인 353)
- [x] 3D 시뮬레이션: `ChatGarment/run_garmentcode_sim.py`

---

## 5. 빠른 참조 가이드

### 5.1 주요 파일 경로 요약

```
agentic_system/
├── core/
│   ├── agent_runtime.py          # Agent 1 (종합 감독)
│   └── f_llm.py                  # Agent 2 (작업 지시 전문가) ⚠️ 파일명 주의
├── tools/
│   ├── extensions.py             # Extension Tool (2D→3D)
│   └── chatgarment_integration.py # ChatGarment Pipeline ⚠️ 오타 수정
└── api/
    └── main.py                   # API Server

ChatGarment/
├── llava/
│   └── garment_utils_v2.py      # GarmentCodeRC 함수 ⚠️ 경로 주의
└── run_garmentcode_sim.py       # 3D 시뮬레이션 스크립트
```

### 5.2 핵심 함수 호출 체인

```
1. API Server (main.py)
   └─> agent_runtime.process_request()
       └─> agent_runtime._analyze_user_intent()        # 인식
       └─> agent_runtime._create_abstract_plan()        # 판단
       └─> agent2.generate_execution_plan()            # Agent 2 호출
       └─> agent_runtime._execute_plan()               # 행동
           └─> extensions_2d_to_3d_tool()
               └─> extensions.execute()
                   └─> extensions._analyze_image()
                       └─> chatgarment_pipeline.analyze_image()
                   └─> extensions._generate_pattern()
                       └─> run_garmentcode_parser_float50()
                   └─> extensions._convert_to_3d()
                       └─> run_garmentcode_sim.py (서브프로세스)
```

---

## 6. 결론

다이어그램과 실제 코드베이스 간의 파일명 차이를 정리하고, 각 컴포넌트의 정확한 위치를 매핑했습니다. 

**주요 수정 필요 사항**:
1. `core_llm.py` → `core/f_llm.py` (파일명 수정)
2. `chatgarment_integraion.py` → `chatgarment_integration.py` (오타 수정)
3. `ChatGarment_llava_utile_v2.py` → `ChatGarment/llava/garment_utils_v2.py` (경로 및 파일명 수정)

이 문서를 참고하여 다이어그램을 실제 코드베이스와 일치시키실 수 있습니다.

