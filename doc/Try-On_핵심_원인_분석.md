# Try-On 미동작 핵심 원인 분석

## 1. 현상 요약

- **증상**: 의류+인물 두 장을 올려도 합성이 안 되고, 옷 사진 그대로만 나오거나 의류 실루엣만 표시됨.
- **환경**: SIMS Fashion(sims-fashion.pages.dev)에서는 **동일 GEMINI_API_KEY**로 Try-On이 잘 동작함. 로컬 POC에서는 동일 키를 쓰는데도 개선이 없음.

---

## 2. 핵심 원인 후보

### (1) POC 뼈대 구조 (가장 유력)

**흐름**: 사용자 입력 → Custom UI(payload) → Agent Runtime → **의도 분석** → **추상 계획** → **Agent 2(실행 계획 생성)** → 실행 계획의 step **parameters** → 도구(gemini_tryon) 호출.

- **문제 가능성**  
  - `input_data`(image_path, person_image_path)가 **실행 계획 생성 단계**에서 step의 `parameters`로 **그대로 전달되지 않을 수 있음**.  
  - Agent 2(InternVL/FLLM)가 **JSON 실행 계획**을 만들 때 `context`를 참조하지만, 스키마/프롬프트에 `person_image_path`가 명시되지 않으면 **빠질 수 있음**.  
  - 한 단계라도 `person_image_path`가 누락되면 Try-On 도구는 **인물 없음**으로 처리 → 의류만 복사·fallback.

**검증 방법**: Agent 경유 없이 **직통 Try-On API**로 같은 입력(의류+인물)을 보내 본다.  
- 직통으로는 합성되는데 기존 `/api/v1/request`로는 안 되면 → **POC 뼈대(실행 계획/context 전달)** 쪽이 원인.  
- 직통으로도 안 되면 → **Gemini 호출/키/모델/프론트 전송** 쪽을 의심.

### (2) 인자 전달 단절

- **payload.input_data** → `generate_execution_plan(context=input_data)` → `_create_3d_generation_steps(plan, context)` → step `parameters` → 도구 `parameters` / `context`.
- 이 중 한 구간에서 **키 이름 불일치**(예: `personImagePath` vs `person_image_path`) 또는 **직렬화 시 필드 누락**이 있으면 인물 경로가 도구까지 도달하지 않음.
- **확인 방법**: API 수신 직후, `generate_execution_plan` 직후, `_execute_plan`에서 도구 호출 직전에 `input_data`/`parameters`에 `person_image_path`가 있는지 로그로 확인.

### (3) 프론트엔드 multipart 전송

- `person_image`가 **실제 요청 body에 포함되지 않는 경우** (필드명 오타, 상태 미반영, 한 번에 하나의 파일만 전송되는 버그 등) 서버에는 `person_image_path`가 생성되지 않음.
- **확인 방법**: 브라우저 개발자 도구 → 네트워크 탭에서 `/api/v1/request` 요청의 **Payload**에 `person_image` 파일이 있는지 확인. 서버 로그에서 `[API] person_image={True/False}` 출력 확인.

### (4) 환경/실행 조건

- **GEMINI_API_KEY**: 서버 프로세스에 `.env`가 제대로 로드되지 않았거나, 다른 cwd에서 실행돼 키를 못 읽는 경우.
- **TRY_ON_ONLY**: 값이 없거나 오타면 의도 분기가 “대화”로 빠져 Try-On 단계가 아예 실행되지 않을 수 있음.
- **확인 방법**: 서버 시작 시 로그에 `GEMINI_API_KEY 설정 여부: 예` 출력되는지, `TRY_ON_ONLY=1` 적용 후 재시작했는지 확인.

---

## 3. 직통 Try-On API로 원인 격리

**목적**: POC 뼈대(Agent 1 → Agent 2 → 실행 계획 → 도구)를 거치지 않고, **같은 도구(gemini_tryon)**만 호출해 보면 “구조 때문인지” 여부를 나눌 수 있음.

### 구현 내용

- **엔드포인트**: `POST /api/v1/tryon`
- **요청**: `image`(의류), `person_image`(인물) 필수, `session_id` 선택.
- **동작**: 업로드 저장 후 `gemini_tryon_tool("try_on", params, context)` 직접 호출. 응답은 기존과 동일한 형식으로 `format_output` 후 반환.

### 프론트엔드 동작

- **의류+인물 둘 다 있을 때**: 기존 `/api/v1/request` 대신 **`/api/v1/tryon`** 호출 (직통 경로).
- **의류만 / 인물만 / 텍스트만**: 기존대로 `/api/v1/request` 사용.

### 해석

| 직통 `/api/v1/tryon` 결과 | 기존 `/api/v1/request` 결과 | 해석 |
|---------------------------|-----------------------------|------|
| 합성 성공                 | 실패                        | **POC 뼈대(실행 계획/context 전달)** 쪽이 핵심 원인. |
| 실패                      | 실패                        | Gemini 키·모델·쿼터 또는 **프론트에서 인물 파일 미전송** 가능성. |
| 합성 성공                 | 성공                        | 일시적 이슈였거나, 직통 경로와 동일 조건으로 수렴한 경우. |

---

## 4. 다음에 할 수 있는 작업

1. **직통 Try-On으로 실제 테스트**  
   의류+인물 두 장 올린 뒤 전송 → 직통으로 합성되는지, 기존 경로로는 안 되는지 확인.
2. **실행 계획 로그 강화**  
   `_create_3d_generation_steps` 직후 `parameters`에 `person_image_path`가 포함되는지, `_execute_plan`에서 도구에 넘기는 `parameters`/`context`를 로그로 출력.
3. **POC 단순화(선택)**  
   Try-On 전용 모드일 때는 “의류+인물 있음 → 실행 계획 생성 없이 곧바로 gemini_tryon 호출”하는 **우회 분기**를 두어, 구조적 원인을 우회할 수 있음.

---

## 5. 참고 파일

- 실행 계획 생성: `agentic_system/core/f_llm.py` — `_create_3d_generation_steps(plan, context)`
- Try-On 도구: `agentic_system/tools/gemini_tryon.py` — `_try_on(parameters, context)`
- API 진입: `agentic_system/api/main.py` — `/api/v1/request`, `/api/v1/tryon`
- 프론트 전송: `agentic_system/frontend/src/App.jsx` — `useDirectTryon` 분기
