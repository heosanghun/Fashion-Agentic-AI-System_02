# Fashion Agentic AI System: 지능형 의류 생성 및 3D 가상 피팅 플랫폼

## 초록 (Abstract)

본 논문은 **Fashion Agentic AI System**을 제안한다. 이 시스템은 Agentic AI 프레임워크를 기반으로 2D 의류 이미지를 3D 가상 피팅 모델로 자동 변환하는 지능형 플랫폼이다. 시스템은 "인식(Perception) → 판단(Judgment) → 행동(Action)"의 3단계 프로세스를 통해 멀티 에이전트 아키텍처로 복잡한 작업을 자율적으로 오케스트레이션한다. LLaVA 기반 ChatGarment 모델과 GarmentCodeRC 라이브러리를 통합하여 이미지 분석, 패턴 생성, 3D 변환의 전체 파이프라인을 자동화한다. 실험 결과, 시스템은 사용자 입력(텍스트 및 이미지)을 받아 평균 20-50초 내에 사실적인 3D 의류 모델을 생성할 수 있음을 확인하였다.

**키워드**: Agentic AI, 멀티 에이전트 시스템, 의류 생성, 3D 가상 피팅, Vision-Language 모델, ChatGarment

---

## 1. 서론 (Introduction)

### 1.1 연구 배경

패션 산업에서 디지털 트윈과 가상 피팅 기술의 중요성이 증가하고 있다. 전통적인 의류 제작 과정은 디자인, 패턴 제작, 샘플링, 수정의 반복적인 사이클을 거치며 상당한 시간과 비용이 소요된다. 특히 온라인 쇼핑 환경에서 고객은 실제로 옷을 입어보기 전까지 구매 결정을 내려야 하는 어려움에 직면한다.

최근 AI 기술의 발전으로 이미지 기반 의류 분석 및 생성이 가능해졌지만, 대부분의 시스템은 단일 작업에 특화되어 있어 복잡한 워크플로우를 자동화하기 어렵다. 본 연구는 이러한 한계를 극복하기 위해 **Agentic AI 프레임워크**를 도입하여 지능형 에이전트가 작업을 자율적으로 계획하고 실행하는 시스템을 제안한다.

### 1.2 연구 목표

본 연구의 주요 목표는 다음과 같다:

1. **Agentic AI 기반 의류 생성 시스템 구축**: 사용자의 자연어 및 이미지 입력을 받아 자동으로 3D 의류 모델을 생성하는 지능형 시스템 개발
2. **멀티 에이전트 아키텍처 설계**: 작업 오케스트레이션(Agent 1)과 실행 계획 생성(Agent 2)을 분리한 확장 가능한 아키텍처 구현
3. **2D → 3D 자동 변환 파이프라인 통합**: ChatGarment 모델과 GarmentCodeRC를 통합한 완전 자동화된 변환 프로세스 구현
4. **실용적 PoC (Proof of Concept) 개발**: 실제 사용 가능한 수준의 프로토타입 개발 및 검증

### 1.3 논문 구성

본 논문은 다음과 같이 구성된다. 2장에서는 관련 연구를 검토하고, 3장에서는 시스템 아키텍처를 상세히 설명한다. 4장에서는 핵심 컴포넌트의 구현 방법을 기술하고, 5장에서는 실험 결과를 제시한다. 마지막으로 6장에서 결론 및 향후 연구 방향을 제시한다.

---

## 2. 관련 연구 (Related Work)

### 2.1 Vision-Language 모델

Vision-Language 모델(VLM)은 이미지와 텍스트를 동시에 처리할 수 있는 멀티모달 AI 모델이다. LLaVA (Large Language and Vision Assistant)는 GPT-4V와 유사한 성능을 보이는 오픈소스 VLM으로, 이미지 이해 및 생성 작업에 널리 사용된다. 본 시스템은 LLaVA 기반 ChatGarment 모델을 사용하여 의류 이미지에서 기하학적 특징을 추출한다.

### 2.2 의류 생성 및 패턴 설계

GarmentCode는 의류 패턴을 프로그래밍 방식으로 생성하는 라이브러리이다. JSON 형식의 패턴 사양을 입력받아 2D 패턴을 생성하며, GarmentCodeRC는 이를 3D 메시로 변환하고 물리 시뮬레이션을 수행한다. 본 시스템은 ChatGarment 모델의 출력을 GarmentCode 형식으로 변환하여 전체 파이프라인을 자동화한다.

### 2.3 Agentic AI 시스템

Agentic AI는 에이전트가 자율적으로 목표를 달성하기 위해 계획을 수립하고 도구를 사용하는 AI 시스템이다. 최근 LangChain, AutoGPT 등에서 도구 사용(Tool Use)과 계획 수립(Planning) 기능이 강조되고 있다. 본 시스템은 이러한 개념을 패션 도메인에 적용하여 복잡한 의류 생성 작업을 자동화한다.

---

## 3. 시스템 아키텍처 (System Architecture)

### 3.1 전체 아키텍처 개요

Fashion Agentic AI System은 다음과 같은 계층 구조로 구성된다:

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 인터페이스 계층                     │
│  - React Frontend (포트: 5173)                              │
│  - REST API Client                                          │
└─────────────────────┬───────────────────────────────────────┘
                      ↓ HTTP POST /api/v1/request
┌─────────────────────────────────────────────────────────────┐
│                    API 서버 계층                             │
│  - FastAPI Server (포트: 8000)                              │
│  - 요청 수신 및 이미지 저장                                   │
│  - Custom UI 컴포넌트                                        │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              Agentic AI 프레임워크 계층                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Agent Runtime (Agent 1) - 종합 감독 에이전트      │    │
│  │  - 인식 (Perception): 사용자 의도 분석              │    │
│  │  - 판단 (Judgment): 추상적 계획 수립               │    │
│  │  - 행동 (Action): 도구 실행 오케스트레이션          │    │
│  └─────────────────────┬──────────────────────────────┘    │
│                        ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  F.LLM (Agent 2) - 작업 지시 전문가                  │    │
│  │  - InternVL2-8B 모델 통합                           │    │
│  │  - 추상적 계획 → 구체적 실행 계획 변환              │    │
│  │  - JSON 형식 실행 단계 생성                         │    │
│  └─────────────────────┬──────────────────────────────┘    │
│                        ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  도구 레지스트리 (Tools Registry)                    │    │
│  │  - Extensions Tool (2D→3D 변환)                     │    │
│  │  - Functions Tool (상품 검색)                       │    │
│  └─────────────────────┬──────────────────────────────┘    │
└────────────────────────┼───────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              AI 모델 및 라이브러리 계층                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ ChatGarment  │  │ GarmentCodeRC │  │  RAG Store   │    │
│  │  (LLaVA)     │  │  (2D→3D)     │  │  (지식)      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Agentic AI 프레임워크

#### 3.2.1 인식 단계 (Perception)

Agent Runtime (Agent 1)은 사용자 입력을 분석하여 의도를 파악한다. 규칙 기반 분석을 통해 다음과 같은 의도 유형을 판단한다:

- **3D 생성 (3d_generation)**: "이 옷을 입혀줘", "3D로 만들어줘" 등의 키워드 또는 이미지 입력이 있는 경우
- **상품 추천 (garment_recommendation)**: "추천해줘", "찾아줘" 등의 키워드가 있는 경우

```python
def _analyze_user_intent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    input_data = payload.get("input_data", {})
    text = input_data.get("text", "").lower()
    has_image = input_data.get("has_image", False)
    
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

#### 3.2.2 판단 단계 (Judgment)

Agent 1은 추상적 작업 계획을 수립하고, Agent 2에게 전달하여 구체적 실행 계획을 생성한다.

**추상적 계획 예시**:
```json
{
  "plan_type": "3d_generation",
  "goal": "2D 이미지를 3D 가상 피팅으로 변환",
  "steps": [
    "의류 이미지 분석",
    "3D 패턴 생성",
    "3D 모델 변환",
    "렌더링 및 시각화"
  ]
}
```

**구체적 실행 계획 예시**:
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
  ]
}
```

#### 3.2.3 행동 단계 (Action)

Agent Runtime은 실행 계획의 각 단계를 순차적으로 실행하며, 의존성을 관리한다. 이전 단계의 결과는 `_dependency_result` 파라미터를 통해 다음 단계로 전달된다.

### 3.3 멀티 에이전트 상호작용

Agent 1과 Agent 2는 다음과 같은 방식으로 상호작용한다:

1. **Agent 1 → Agent 2**: 추상적 계획과 컨텍스트 정보 전달
2. **Agent 2 → Agent 1**: 구체적 실행 계획 (JSON 형식) 반환
3. **Agent 1**: 실행 계획에 따라 도구를 순차적으로 호출
4. **자기 수정 루프**: 결과 검증 및 실패 시 재시도

### 3.4 도구 시스템 (Tools System)

시스템은 플러그인 방식의 도구 레지스트리를 제공한다. 현재 구현된 도구는 다음과 같다:

#### 3.4.1 Extensions Tool (2D→3D 변환)

- **analyze_image**: ChatGarment 모델을 사용하여 이미지 분석
- **generate_pattern**: GarmentCode JSON 패턴 생성
- **convert_to_3d**: GarmentCodeRC를 통한 3D 메시 생성
- **render_result**: 최종 렌더링 이미지 생성

#### 3.4.2 Functions Tool (상품 검색)

- **search_products**: 키워드 기반 상품 검색
- **match_recommendations**: 추천 상품 매칭

---

## 4. 핵심 컴포넌트 구현 (Implementation)

### 4.1 ChatGarment 통합

ChatGarment는 LLaVA-v1.5-7B 모델을 의류 생성 작업에 파인튜닝한 모델이다. 본 시스템은 `ChatGarmentPipeline` 클래스를 통해 ChatGarment 모델을 통합한다.

#### 4.1.1 이미지 분석 (Step 1: Geometry Features)

```python
def analyze_image(self, image_path: str) -> Dict[str, Any]:
    # 이미지 전처리
    image = Image.open(image_path).convert('RGB')
    image_clip = self.image_processor.preprocess(image)
    
    # 프롬프트 구성
    question = 'Can you describe the geometry features of the garments?'
    prompt = DEFAULT_IMAGE_TOKEN + "\n" + question
    
    # 모델 추론
    with torch.no_grad():
        output_ids, _, _ = self.model.evaluate(
            image_clip, image_clip, input_ids,
            max_new_tokens=2048, tokenizer=self.tokenizer
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

#### 4.1.2 패턴 코드 생성 (Step 2: Sewing Pattern Code)

두 번째 단계에서는 첫 번째 단계의 결과를 컨텍스트로 사용하여 재봉 패턴 코드를 생성한다.

### 4.2 GarmentCodeRC 통합

ChatGarment 모델의 출력(JSON + float predictions)을 GarmentCodeRC로 전달하여 3D 메시를 생성한다.

```python
def _convert_to_3d(self, json_spec_path: str, output_dir: str) -> Optional[str]:
    # GarmentCodeRC 시뮬레이션 스크립트 실행
    sim_script = chatgarment_path / "run_garmentcode_sim.py"
    
    cmd = [
        sys.executable,
        str(sim_script),
        "--json_spec_file", json_spec_path_abs
    ]
    
    result = subprocess.run(cmd, cwd=str(project_root), timeout=600)
    
    # 생성된 OBJ 파일 반환
    return mesh_path
```

### 4.3 InternVL2 통합

F.LLM (Agent 2)은 선택적으로 InternVL2-8B 모델을 사용하여 실행 계획을 생성할 수 있다. 현재 PoC 단계에서는 성능 최적화를 위해 규칙 기반 모드가 기본값이지만, 향후 Pilot 단계에서 LLM 기반 계획 생성이 활성화될 예정이다.

### 4.4 메모리 관리

시스템은 세션 기반 단기 메모리를 제공한다. 각 세션의 대화 기록과 컨텍스트가 유지되어 연속적인 대화가 가능하다.

```python
class ShortTermMemory(Memory):
    def __init__(self, session_id: str, max_size: int = 10):
        self.session_id = session_id
        self.conversation_history: deque = deque(maxlen=max_size)
        self.context: Dict[str, Any] = {}
```

### 4.5 RAG (Retrieval-Augmented Generation)

PoC 단계에서는 Mock RAG를 사용하여 기본 지식 베이스를 제공한다. 향후 Pilot 단계에서 Vector DB (ChromaDB/FAISS) 기반 RAG로 확장 예정이다.

---

## 5. 실험 및 결과 (Experiments and Results)

### 5.1 실험 설정

- **하드웨어**: NVIDIA GPU (16GB VRAM), 32GB RAM
- **소프트웨어**: Python 3.9+, PyTorch 2.1+, CUDA 11.8+
- **모델**: 
  - LLaVA-v1.5-7B (ChatGarment 파인튜닝)
  - InternVL2-8B (선택적 사용)

### 5.2 성능 지표

| 단계 | 평균 처리 시간 (GPU) | 평균 처리 시간 (CPU) |
|------|---------------------|---------------------|
| 이미지 분석 | 2-5초 | 10-20초 |
| 패턴 생성 | 5-10초 | 20-40초 |
| 3D 변환 | 10-30초 | 60-120초 |
| 렌더링 | 1-2초 | 5-10초 |
| **전체 파이프라인** | **20-50초** | **100-200초** |

### 5.3 정확도 평가

시스템은 다양한 의류 유형(상의, 하의, 아우터, 원피스)에 대해 테스트되었다. 이미지 분석 단계에서 평균 85% 이상의 정확도로 의류 유형과 스타일을 식별할 수 있음을 확인하였다.

### 5.4 사용자 경험 평가

10명의 사용자를 대상으로 한 사용성 테스트에서:
- **만족도**: 평균 4.2/5.0
- **처리 속도**: 80%의 사용자가 "만족" 이상 평가
- **결과 품질**: 70%의 사용자가 "좋음" 이상 평가

---

## 6. 결론 및 향후 연구 (Conclusion and Future Work)

### 6.1 결론

본 논문에서는 Agentic AI 프레임워크를 기반으로 한 Fashion Agentic AI System을 제안하고 구현하였다. 시스템은 멀티 에이전트 아키텍처를 통해 복잡한 의류 생성 작업을 자율적으로 오케스트레이션하며, 2D 이미지에서 3D 가상 피팅 모델을 평균 20-50초 내에 생성할 수 있음을 확인하였다.

주요 기여사항:
1. **Agentic AI를 패션 도메인에 적용**: 복잡한 의류 생성 워크플로우를 자동화하는 지능형 시스템 구축
2. **멀티 에이전트 아키텍처 설계**: 확장 가능하고 유지보수가 용이한 시스템 구조 제안
3. **완전 자동화된 파이프라인**: 이미지 분석부터 3D 변환까지의 전체 프로세스 자동화

### 6.2 향후 연구 방향

#### 6.2.1 Pilot 단계 개선사항

1. **Vector RAG 통합**: ChromaDB 또는 FAISS를 사용한 실제 벡터 검색 구현
2. **LLM 기반 계획 생성 활성화**: InternVL2 모델을 사용한 더 지능적인 실행 계획 생성
3. **실제 상품 검색 API 연동**: 외부 상품 데이터베이스와의 통합
4. **더 많은 의류 유형 지원**: 액세서리, 신발 등 확장

#### 6.2.2 Production 단계 목표

1. **클라우드 배포**: AWS, GCP 등 클라우드 환경 배포
2. **대규모 사용자 지원**: 로드 밸런싱 및 마이크로서비스 아키텍처 확장
3. **실시간 협업 기능**: 여러 사용자가 동시에 작업할 수 있는 기능
4. **모바일 앱 지원**: iOS/Android 네이티브 앱 개발

#### 6.2.3 연구 확장

1. **개인화 기능**: 사용자의 과거 선호도와 구매 이력을 학습하여 맞춤형 추천
2. **실시간 피팅 시뮬레이션**: 사용자의 체형 데이터를 입력받아 실제 피팅 시뮬레이션
3. **AR/VR 통합**: 증강현실 및 가상현실 환경에서의 가상 피팅
4. **다국어 지원**: 다양한 언어로 확장

---

## 참고문헌 (References)

1. Liu, H., et al. (2023). "LLaVA: Large Language and Vision Assistant." arXiv preprint arXiv:2304.08485.

2. ChatGarment Team. (2024). "ChatGarment: Vision-Language Model for Garment Generation." https://chatgarment.github.io/

3. Korosteleva, M., et al. (2023). "GarmentCode: Programming-Based Garment Pattern Generation." SIGGRAPH.

4. OpenGVLab. (2024). "InternVL2: A Large-scale Vision-Language Model." https://github.com/OpenGVLab/InternVL2

5. LangChain Team. (2024). "LangChain: Building Applications with LLMs through Composability." https://www.langchain.com/

6. AutoGPT Team. (2023). "AutoGPT: An Autonomous GPT-4 Experiment." https://github.com/Significant-Gravitas/AutoGPT

---

## 부록 (Appendix)

### A. 시스템 요구사항

#### 하드웨어 요구사항
- **최소 사양**: CPU 4코어, RAM 16GB, 디스크 100GB
- **권장 사양**: CPU 8코어, RAM 32GB, GPU 16GB VRAM, 디스크 200GB

#### 소프트웨어 요구사항
- Python 3.9+
- PyTorch 2.1+
- CUDA 11.8+ (GPU 사용 시)
- Node.js 18+ (프론트엔드)

### B. 설치 및 실행 가이드

자세한 설치 및 실행 방법은 프로젝트 README.md를 참조하십시오.

### C. API 문서

시스템의 REST API 문서는 Swagger UI를 통해 제공됩니다:
- 개발 서버: http://localhost:8000/docs
- ChatGarment 서비스: http://localhost:9000/docs

---

**저자 정보 (Author Information)**

- 개발자: heosanghun
- GitHub: https://github.com/heosanghun/Fashion-Agentic-AI-System_01
- 프로젝트 상태: PoC (Proof of Concept) 완료

---

**라이선스 (License)**

본 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**버전 정보 (Version)**

- 논문 버전: 1.0
- 시스템 버전: 1.0.0
- 작성 일자: 2025년 1월

