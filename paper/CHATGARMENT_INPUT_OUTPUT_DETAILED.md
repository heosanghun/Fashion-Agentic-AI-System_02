# ChatGarment 경로 입력/출력 처리 상세 분석

## 📁 경로: `D:\AI\ChatGarment\ChatGarment`

이 디렉토리는 ChatGarment 모델의 핵심 기능을 담당하며, 2D 이미지 입력부터 3D 의상 파일 출력까지 전체 파이프라인을 처리합니다.

---

## 🔵 입력 처리 (Input Processing)

### 1. 이미지 입력 처리

#### 1.1 이미지 로딩 및 전처리

**파일 위치**: `agentic_system/tools/chatgarment_integration.py` (라인 290-311)

**처리 과정**:

```python
# 1. 이미지 파일 로딩
image = Image.open(image_path).convert('RGB')

# 2. 이미지 정사각형 패딩 처리
def expand2square(pil_img, background_color=(122, 116, 104)):
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result

image = expand2square(image, tuple(int(x*255) for x in self.image_processor.image_mean))

# 3. Vision Encoder를 위한 전처리
image_clip = self.image_processor.preprocess(image, return_tensors='pt')['pixel_values'][0]
image_clip = image_clip.unsqueeze(0).to(self.device)
image_clip = image_clip.bfloat16()
```

**주요 기능**:
- **RGB 변환**: 모든 이미지를 RGB 형식으로 통일
- **정사각형 패딩**: 비율 유지하며 정사각형으로 변환 (배경색: 회색)
- **텐서 변환**: PyTorch 텐서로 변환 및 디바이스 이동 (CUDA/CPU)
- **정밀도 설정**: bfloat16으로 메모리 최적화

#### 1.2 이미지 전처리 유틸리티

**파일 위치**: `ChatGarment/llava/mm_utils.py`

**주요 함수**:

##### `resize_and_pad_image(image, target_resolution)`
- **역할**: 이미지를 목표 해상도로 리사이즈 및 패딩
- **입력**: PIL Image, 목표 해상도 (width, height)
- **출력**: 리사이즈 및 패딩된 PIL Image
- **특징**: 종횡비 유지하며 중앙 정렬 패딩

##### `select_best_resolution(original_size, possible_resolutions)`
- **역할**: 원본 이미지 크기에 가장 적합한 해상도 선택
- **입력**: 원본 크기, 가능한 해상도 목록
- **출력**: 최적 해상도 (width, height)

##### `divide_to_patches(image, patch_size)`
- **역할**: 이미지를 패치로 분할 (고해상도 이미지 처리용)
- **입력**: PIL Image, 패치 크기
- **출력**: 패치 리스트

#### 1.3 텍스트 프롬프트 입력

**파일 위치**: `agentic_system/tools/chatgarment_integration.py` (라인 314-325)

**Step 1 프롬프트** (Geometry Features 추출):
```python
question1 = 'Can you describe the geometry features of the garments worn by the model in the Json format?'
```

**Step 2 프롬프트** (Sewing Pattern Code 생성):
```python
question2 = 'Can you estimate the sewing pattern code based on the image and Json format garment geometry description?'
```

**프롬프트 구성**:
```python
conv = conversation_lib.conv_templates["v1"].copy()
conv.messages = []
prompt = DEFAULT_IMAGE_TOKEN + "\n" + question
conv.append_message(conv.roles[0], prompt)
conv.append_message(conv.roles[1], None)
prompt_full = conv.get_prompt()
```

---

## 🟢 출력 처리 (Output Processing)

### 2. 중간 출력 (Intermediate Outputs)

#### 2.1 Step 1 출력: Geometry Features (JSON)

**파일 위치**: `agentic_system/tools/chatgarment_integration.py` (라인 336-344)

**출력 형식**:
```json
{
  "upperbody_garment": {
    "type": "T-shirt",
    "sleeves": "short",
    "collar": "round",
    ...
  },
  "lowerbody_garment": {
    ...
  }
}
```

**처리 과정**:
```python
# 1. 모델 추론
output_ids, _, _ = self.model.evaluate(
    image_clip,
    image_clip,
    input_ids1,
    max_new_tokens=2048,
    tokenizer=self.tokenizer,
)

# 2. 텍스트 디코딩
text_output1 = self.tokenizer.decode(output_ids1, skip_special_tokens=False)
text_output1 = text_output1.replace('[STARTS]', '').replace('[SEG]', '').replace('[ENDS]', '')

# 3. JSON 수정 및 파싱
json_output = repair_json(text_output1, return_objects=True)
```

**저장 위치**: `outputs/garments/valid_garment_{garment_id}/output.txt`

#### 2.2 Step 2 출력: Sewing Pattern Code (JSON + Float Predictions)

**파일 위치**: `agentic_system/tools/chatgarment_integration.py` (라인 479-516)

**출력 형식**:
- **JSON**: 패턴 코드 구조
- **Float Predictions**: 50개의 부동소수점 예측값 (디자인 파라미터)

**처리 과정**:
```python
# 1. 모델 추론 (Float 예측 포함)
output_ids2, float_preds, seg_token_mask = self.model.evaluate(
    image_clip,
    image_clip,
    input_ids2,
    max_new_tokens=2048,
    tokenizer=self.tokenizer,
)

# 2. 텍스트 디코딩
text_output2 = self.tokenizer.decode(output_ids2, skip_special_tokens=False)
text_output2 = text_output2.replace('[STARTS]', '').replace('[SEG]', '').replace('[ENDS]', '')

# 3. JSON 수정 및 파싱
json_output = repair_json(text_output2, return_objects=True)

# 4. Float 예측값 처리
float_preds = float_preds.cpu().numpy()  # NumPy 배열로 변환
```

**저장 위치**: `outputs/garments/valid_garment_{garment_id}/output.txt` (Step 1과 함께 저장)

### 3. 패턴 생성 출력 (Pattern Generation Output)

#### 3.1 GarmentCode 패턴 JSON 생성

**파일 위치**: `ChatGarment/llava/garment_utils_v2.py` (라인 187-241)

**함수**: `try_generate_garments()`

**입력**:
- `body_measurement_path`: 바디 측정값 경로 (YAML)
- `garment_output`: 의류 출력 JSON (Step 2 결과)
- `garment_name`: 의류 이름 ('upper', 'lower', 'wholebody')
- `output_path`: 출력 디렉토리
- `float_dict`: Float 예측값 딕셔너리 (50개)

**처리 과정**:

```python
# 1. 디자인 파라미터 처리
design = recursive_change_params_1float(
    default_config, 
    design_pred_raw, 
    float_dict,
    invnorm_float=True
)

# 2. 바디 파라미터 로딩
body = BodyParameters(bodies_measurements[body_measurement])

# 3. MetaGarment 객체 생성
test_garment = MetaGarment('valid_garment', body, design)

# 4. 패턴 어셈블리
pattern = test_garment.assembly()

# 5. 패턴 직렬화 (JSON 파일로 저장)
folder = pattern.serialize(
    output_path,
    tag=garment_name,
    to_subfolder=True,
    with_3d=False, 
    with_text=False, 
    view_ids=False
)
```

**출력 파일**:
- `outputs/patterns/valid_garment_{garment_name}/valid_garment_{garment_name}_specification.json`
- `outputs/patterns/valid_garment_{garment_name}/design.yaml`
- `outputs/patterns/valid_garment_{garment_name}/body.yaml`

**패턴 JSON 구조**:
```json
{
  "components": [
    {
      "name": "front",
      "vertices": [...],
      "edges": [...],
      "panels": [...]
    },
    {
      "name": "back",
      ...
    }
  ],
  "seams": [...],
  "metadata": {...}
}
```

#### 3.2 패턴 파서 함수

**파일 위치**: `ChatGarment/llava/garment_utils_v2.py` (라인 353-391)

**함수**: `run_garmentcode_parser_float50()`

**입력**:
- `all_json_spec_files`: JSON specification 파일 경로 리스트 (누적)
- `json_output`: Step 2의 JSON 출력
- `float_preds`: Float 예측값 배열 (50개 또는 100개)
- `output_dir`: 출력 디렉토리

**처리 로직**:

```python
if 'upperbody_garment' in json_output:
    # 상하의 분리 처리
    upper_config = json_output['upperbody_garment']
    lower_config = json_output['lowerbody_garment']
    
    float_preds = float_preds.reshape(2, -1)  # 상의/하의 각 50개
    float_dict_upper = {k: v for k, v in zip(all_float_paths, float_preds[0])}
    float_dict_lower = {k: v for k, v in zip(all_float_paths, float_preds[1])}
    
    # 상의 패턴 생성
    try_generate_garments(None, upper_config, 'upper', output_dir, 
                         invnorm_float=True, float_dict=float_dict_upper)
    # 하의 패턴 생성
    try_generate_garments(None, lower_config, 'lower', output_dir, 
                         invnorm_float=True, float_dict=float_dict_lower)
    
    # 생성된 파일 경로 추가
    all_json_spec_files.append(
        os.path.join(output_dir, 'valid_garment_upper', 
                    'valid_garment_upper_specification.json')
    )
    all_json_spec_files.append(
        os.path.join(output_dir, 'valid_garment_lower', 
                    'valid_garment_lower_specification.json')
    )
else:
    # 원피스 처리
    wholebody_config = json_output['wholebody_garment']
    
    float_preds = float_preds.reshape(-1)  # 50개
    float_dict = {k: v for k, v in zip(all_float_paths, float_preds)}
    
    try_generate_garments(None, wholebody_config, 'wholebody', output_dir, 
                         invnorm_float=True, float_dict=float_dict)
    
    all_json_spec_files.append(
        os.path.join(output_dir, 'valid_garment_wholebody', 
                    'valid_garment_wholebody_specification.json')
    )
```

**출력**: 생성된 JSON specification 파일 경로 리스트

### 4. 최종 출력: 3D 모델 파일 (.obj)

#### 4.1 3D 시뮬레이션 실행

**파일 위치**: `ChatGarment/run_garmentcode_sim.py`

**입력**:
- `--json_spec_file`: 패턴 specification JSON 파일 경로
- `--easy_texture_path`: 텍스처 경로 (선택사항)

**처리 과정**:

```python
def run_simultion_warp(pattern_spec, sim_config, output_path, easy_texture_path):
    # 1. 패턴 파일 경로 파싱
    spec_path = Path(pattern_spec)
    garment_name, _, _ = spec_path.stem.rpartition('_')
    
    # 2. 경로 설정
    paths = PathCofig(
        in_element_path=spec_path.parent,
        out_path=output_path,
        in_name=garment_name,
        body_name='mean_all',
        smpl_body=False,
        add_timestamp=False,
        system_path='...',
        easy_texture_path=easy_texture_path
    )
    
    # 3. Box Mesh 생성
    garment_box_mesh = BoxMesh(paths.in_g_spec, props['sim']['config']['resolution_scale'])
    garment_box_mesh.load()
    garment_box_mesh.serialize(paths, store_panels=False, 
                              uv_config=props['render']['config']['uv_texture'])
    
    # 4. 물리 시뮬레이션 실행
    run_sim(
        garment_box_mesh.name,
        props,
        paths,
        save_v_norms=False,
        store_usd=False,
        optimize_storage=False,
        verbose=False
    )
```

**시뮬레이션 과정**:
1. **Box Mesh 생성**: 2D 패턴을 기반으로 초기 3D 박스 메시 생성
2. **물리 시뮬레이션**: Nvidia Warp 엔진을 사용한 의류 드레이핑 시뮬레이션
   - 중력, 마찰, 충돌 등 물리 효과 적용
   - 인체 모델에 맞춰 의류가 자연스럽게 떨어지도록 시뮬레이션
3. **메시 최적화**: 시뮬레이션 결과를 최적화된 메시로 변환

#### 4.2 3D OBJ 파일 출력

**출력 파일 위치**: 
- `{pattern_dir}/{garment_name}_sim.obj`
- 예: `outputs/patterns/valid_garment_upper/valid_garment_upper_sim.obj`

**OBJ 파일 형식**:
```
# 3D Garment Mesh
# Generated by GarmentCodeRC Simulation
g garment_mesh
v -1.234 2.345 3.456  # 정점 (vertices)
v 1.234 2.345 3.456
...
vt 0.123 0.456      # 텍스처 좌표 (texture coordinates)
...
vn 0.707 0.707 0.0  # 법선 벡터 (normal vectors)
...
f 1/1/1 2/2/2 3/3/3  # 면 (faces: vertex/texture/normal)
...
```

**파일 생성 담당 모듈**:
- `GarmentCodeRC/pygarment/meshgen/simulation.py`: 시뮬레이션 엔진
- `GarmentCodeRC/pygarment/meshgen/garment.py`: 의류 메시 클래스
- `GarmentCodeRC/pygarment/meshgen/boxmeshgen.py`: 박스 메시 생성

---

## 📊 전체 입력/출력 흐름도

```
[입력]
  │
  ├─ 이미지 파일 (JPG/PNG)
  │   └─> Image.open() → PIL Image
  │       └─> convert('RGB')
  │           └─> expand2square() [정사각형 패딩]
  │               └─> image_processor.preprocess() [Vision Encoder 전처리]
  │                   └─> Tensor (bfloat16, CUDA)
  │
  └─ 텍스트 프롬프트
      └─> tokenizer_image_token() [토크나이징]
          └─> Tensor (input_ids)

[처리]
  │
  ├─ Step 1: Geometry Features 추출
  │   └─> model.evaluate() [LLaVA 모델 추론]
  │       └─> tokenizer.decode() [텍스트 디코딩]
  │           └─> repair_json() [JSON 수정]
  │               └─> JSON 출력
  │
  └─ Step 2: Sewing Pattern Code 생성
      └─> model.evaluate() [LLaVA 모델 추론 + Float 예측]
          └─> tokenizer.decode() [텍스트 디코딩]
              └─> repair_json() [JSON 수정]
                  └─> JSON 출력 + Float Predictions (50개)

[중간 출력]
  │
  └─> run_garmentcode_parser_float50()
      ├─> recursive_change_params_1float() [파라미터 변환]
      ├─> try_generate_garments() [패턴 생성]
      │   ├─> MetaGarment() [의류 객체 생성]
      │   ├─> pattern.assembly() [패턴 어셈블리]
      │   └─> pattern.serialize() [JSON 파일 저장]
      └─> 패턴 JSON 파일 생성
          └─> valid_garment_{name}_specification.json

[최종 출력]
  │
  └─> run_garmentcode_sim.py
      ├─> BoxMesh() [박스 메시 생성]
      ├─> run_sim() [물리 시뮬레이션]
      └─> 3D OBJ 파일 생성
          └─> {garment_name}_sim.obj
```

---

## 🔍 주요 파일별 역할

### 입력 처리 파일

| 파일 경로 | 역할 | 주요 함수/클래스 |
|----------|------|-----------------|
| `agentic_system/tools/chatgarment_integration.py` | 이미지 로딩 및 전처리 | `ChatGarmentPipeline.analyze_image()`, `process_image_to_garment()` |
| `ChatGarment/llava/mm_utils.py` | 이미지 전처리 유틸리티 | `resize_and_pad_image()`, `select_best_resolution()` |
| `ChatGarment/llava/model/language_model/llava_llama.py` | 멀티모달 입력 처리 | `LlavaLlamaForCausalLM.forward()`, `prepare_inputs_for_generation()` |

### 출력 처리 파일

| 파일 경로 | 역할 | 주요 함수/클래스 |
|----------|------|-----------------|
| `ChatGarment/llava/garment_utils_v2.py` | 패턴 생성 및 JSON 출력 | `try_generate_garments()`, `run_garmentcode_parser_float50()` |
| `ChatGarment/llava/json_fixer.py` | JSON 수정 및 파싱 | `repair_json()` |
| `ChatGarment/run_garmentcode_sim.py` | 3D 시뮬레이션 및 OBJ 출력 | `run_simultion_warp()` |
| `GarmentCodeRC/pygarment/meshgen/simulation.py` | 물리 시뮬레이션 엔진 | `run_sim()` |
| `GarmentCodeRC/pygarment/meshgen/boxmeshgen.py` | 박스 메시 생성 | `BoxMesh` |

---

## 📝 입력/출력 데이터 형식

### 입력 형식

#### 이미지 입력
- **형식**: JPG, PNG
- **처리**: RGB 변환 → 정사각형 패딩 → Vision Encoder 전처리
- **최종 텐서**: `[1, 3, H, W]` (bfloat16, CUDA)

#### 텍스트 입력
- **형식**: 프롬프트 문자열
- **처리**: 토크나이징 → 텐서 변환
- **최종 텐서**: `[1, seq_len]` (LongTensor, CUDA)

### 출력 형식

#### Step 1 출력 (Geometry Features)
```json
{
  "upperbody_garment": {
    "type": "T-shirt",
    "sleeves": "short",
    "collar": "round",
    "fit": "regular"
  },
  "lowerbody_garment": {}
}
```

#### Step 2 출력 (Sewing Pattern Code)
```json
{
  "wholebody_garment": {
    "design": {
      "type": "T-shirt",
      "front": {
        "width": 50.0,
        "height": 70.0,
        ...
      },
      ...
    }
  }
}
```

**Float Predictions**: NumPy 배열, shape `(50,)` 또는 `(2, 50)`

#### 패턴 JSON 출력
```json
{
  "components": [
    {
      "name": "front",
      "vertices": [[x1, y1], [x2, y2], ...],
      "edges": [[v1, v2], ...],
      "panels": [...]
    }
  ],
  "seams": [...],
  "metadata": {
    "garment_type": "T-shirt",
    "version": "1.0"
  }
}
```

#### 최종 3D OBJ 출력
```
# OBJ 파일 형식
v x y z          # 정점
vt u v           # 텍스처 좌표
vn nx ny nz      # 법선 벡터
f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3  # 면
```

---

## 🎯 핵심 처리 함수 상세

### 1. `try_generate_garments()` - 패턴 생성

**위치**: `ChatGarment/llava/garment_utils_v2.py` (라인 187-241)

**입력 파라미터**:
- `body_measurement_path`: 바디 측정값 YAML 파일 경로 (None이면 기본값 사용)
- `garment_output`: 의류 출력 JSON (Step 2 결과)
- `garment_name`: 의류 이름 ('upper', 'lower', 'wholebody')
- `output_path`: 출력 디렉토리
- `invnorm_float`: Float 값 역정규화 여부
- `float_dict`: Float 예측값 딕셔너리 (50개)

**처리 단계**:
1. 디자인 파라미터 변환 (`recursive_change_params_1float`)
2. 바디 파라미터 로딩 (`BodyParameters`)
3. MetaGarment 객체 생성
4. 패턴 어셈블리 (`pattern.assembly()`)
5. 패턴 직렬화 및 저장 (`pattern.serialize()`)

**출력**:
- `valid_garment_{garment_name}_specification.json`
- `design.yaml`
- `body.yaml`

### 2. `run_garmentcode_parser_float50()` - 패턴 파서

**위치**: `ChatGarment/llava/garment_utils_v2.py` (라인 353-391)

**입력 파라미터**:
- `all_json_spec_files`: JSON specification 파일 경로 리스트 (누적)
- `json_output`: Step 2의 JSON 출력
- `float_preds`: Float 예측값 배열 (NumPy)
- `output_dir`: 출력 디렉토리

**처리 로직**:
- 상하의 분리: `upperbody_garment` + `lowerbody_garment` → 2개 패턴 생성
- 원피스: `wholebody_garment` → 1개 패턴 생성

**출력**: 생성된 JSON specification 파일 경로 리스트

### 3. `run_simultion_warp()` - 3D 시뮬레이션

**위치**: `ChatGarment/run_garmentcode_sim.py` (라인 12-57)

**입력 파라미터**:
- `pattern_spec`: 패턴 specification JSON 파일 경로
- `sim_config`: 시뮬레이션 설정 YAML 파일 경로
- `output_path`: 출력 디렉토리
- `easy_texture_path`: 텍스처 경로 (선택사항)

**처리 단계**:
1. Box Mesh 생성 (`BoxMesh`)
2. 박스 메시 직렬화 (`garment_box_mesh.serialize()`)
3. 물리 시뮬레이션 실행 (`run_sim()`)
4. 3D OBJ 파일 자동 생성

**출력**: `{garment_name}_sim.obj` 파일

---

## 📂 출력 디렉토리 구조

```
outputs/
├── garments/
│   └── valid_garment_{garment_id}/
│       ├── output.txt                    # Step 1 + Step 2 텍스트 출력
│       ├── gt_image.png                  # 원본 이미지 복사본
│       ├── valid_garment_upper/          # 상의 패턴 (있는 경우)
│       │   ├── valid_garment_upper_specification.json
│       │   ├── design.yaml
│       │   ├── body.yaml
│       │   └── valid_garment_upper_sim.obj  # 3D 모델
│       ├── valid_garment_lower/          # 하의 패턴 (있는 경우)
│       │   └── ...
│       └── valid_garment_wholebody/      # 원피스 패턴 (있는 경우)
│           └── ...
└── patterns/
    └── valid_garment_{name}/
        ├── valid_garment_{name}_specification.json
        ├── design.yaml
        └── body.yaml
```

---

## 🔄 데이터 변환 과정

### Float Predictions 처리

**위치**: `ChatGarment/llava/garment_utils_v2.py` (라인 117-184)

**함수**: `recursive_change_params_1float()`

**처리 과정**:
1. Float 예측값을 `all_float_paths`와 매핑
2. 역정규화 (0~1 범위 → 실제 값 범위)
3. 디자인 파라미터에 적용

**예시**:
```python
# Float 예측값: 0.5 (정규화된 값)
# 파라미터 범위: [30.0, 60.0]
# 역정규화: 0.5 * (60.0 - 30.0) + 30.0 = 45.0
```

### JSON 수정 및 파싱

**위치**: `ChatGarment/llava/json_fixer.py`

**함수**: `repair_json()`

**기능**:
- 불완전한 JSON 수정
- 특수 문자 이스케이프 처리
- 중괄호/대괄호 균형 맞추기
- JSON 객체로 변환

---

## ✅ 결론

`D:\AI\ChatGarment\ChatGarment` 경로는 다음과 같은 입력/출력 처리를 담당합니다:

### 입력 담당
1. **이미지 전처리**: PIL Image → RGB 변환 → 정사각형 패딩 → Vision Encoder 텐서
2. **텍스트 프롬프트 처리**: 문자열 → 토크나이징 → 텐서 변환
3. **멀티모달 입력 통합**: 이미지 + 텍스트 → 모델 입력 형식

### 출력 담당
1. **Step 1 출력**: Geometry Features JSON
2. **Step 2 출력**: Sewing Pattern Code JSON + Float Predictions
3. **패턴 JSON**: 2D 패턴 specification 파일
4. **최종 3D OBJ**: 물리 시뮬레이션을 통한 3D 의상 메시 파일

모든 처리 과정은 `agentic_system/tools/chatgarment_integration.py`의 `ChatGarmentPipeline` 클래스를 통해 통합 관리됩니다.

