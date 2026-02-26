# GitHub 업로드 파일 목록

이 문서는 ChatGarment 프로젝트의 GitHub 업로드 대상 파일들을 정리한 것입니다.

## 📋 업로드 대상 파일

### ✅ 1. 소스 코드 파일

#### 1.1 agentic_system/ (Agentic AI 시스템)
- `agentic_system/api/`
  - `__init__.py`
  - `main.py`
- `agentic_system/core/`
  - `__init__.py`
  - `agent_runtime.py`
  - `f_llm.py`
  - `memory.py`
  - `custom_ui.py`
- `agentic_system/tools/`
  - `__init__.py`
  - `extensions.py`
  - `extensions_service.py`
  - `functions.py`
  - `chatgarment_integration.py`
- `agentic_system/data_stores/`
  - `__init__.py`
  - `rag.py`
  - `rag_vector.py`
- `agentic_system/models/`
  - `__init__.py`
  - `internvl2_wrapper.py`
- `agentic_system/chatgarment_service/`
  - `main.py`
  - `requirements.txt`
  - `start_service.sh`

#### 1.2 ChatGarment/ (ChatGarment 모델)
- `ChatGarment/llava/`
  - `__init__.py`
  - `*.py` (모든 Python 소스 파일)
  - `model/*.py` (모델 아키텍처 파일)
- `ChatGarment/scripts/`
  - `*.py`, `*.sh` (모든 스크립트 파일)
- `ChatGarment/run_garmentcode_sim.py`
- `ChatGarment/pyproject.toml`
- `ChatGarment/LICENSE`
- `ChatGarment/README.md`
- `ChatGarment/cog.yaml`

#### 1.3 GarmentCodeRC/ (GarmentCode 라이브러리)
- `GarmentCodeRC/pygarment/`
  - `*.py` (모든 Python 소스 파일, `.dll` 제외)
- `GarmentCodeRC/gui/`
  - `*.py`
- `GarmentCodeRC/*.py` (루트 레벨 Python 파일)
- `GarmentCodeRC/pyproject.toml`
- `GarmentCodeRC/setup.cfg`
- `GarmentCodeRC/LICENSE`
- `GarmentCodeRC/ReadMe.md`
- `GarmentCodeRC/CHANGELOG.md`
- `GarmentCodeRC/system.template.json`

#### 1.4 chatgarment_service/ (독립 서비스)
- `chatgarment_service/main.py`
- `chatgarment_service/requirements.txt`
- `chatgarment_service/README.md`

#### 1.5 루트 레벨 스크립트
- `llava_infer.py`
- `restart_api_clean.ps1`
- `scripts/evaluate_garment_v2_imggen_1float.py`

### ✅ 2. 설정 및 구성 파일

- `agentic_system/requirements.txt`
- `agentic_system/frontend/package.json`
- `agentic_system/frontend/vite.config.js`
- `agentic_system/frontend/package-lock.json` (선택사항, 일반적으로 제외하지만 참고용 포함 가능)

### ✅ 3. 프론트엔드 소스 코드

- `agentic_system/frontend/src/`
  - `*.jsx`, `*.css` (모든 소스 파일)
- `agentic_system/frontend/index.html`
- `agentic_system/frontend/public/`
  - 이미지 파일 (`.png`, `.jpg` 등)
- **제외**: `agentic_system/frontend/node_modules/` (절대 업로드하지 않음)

### ✅ 4. 문서 파일

- `PROJECT_STRUCTURE_ANALYSIS.md`
- `agentic_system/README.md`
- `agentic_system/ARCHITECTURE.md`
- `agentic_system/*.md` (모든 마크다운 문서 파일)
- `ChatGarment/docs/`
  - `*.md`
  - `prompts/*.txt`
- `GarmentCodeRC/docs/`
  - `*.md`
  - `*.pdf` (문서 PDF)
- `doc/`
  - `*.md`
  - `*.txt`
  - `*.pdf` (문서 PDF)

### ✅ 5. 예제 데이터 및 자산

- `ChatGarment/example_data/`
  - `example_imgs/*.png`
  - `example_jsons/*.json`
  - `example_sewing_patterns/*.png`, `*.yaml`
- `ChatGarment/docs/images/`
  - `*.gif`, `*.png`, `*.jpg`
- `GarmentCodeRC/assets/`
  - `garment_programs/*.py`
  - `design_params/*.yaml`
  - `bodies/*.yaml`
  - `Sim_props/*.yaml`
  - `Patterns/*.json`
- `LOGO/`
  - `*.png`

### ✅ 6. 스크립트 파일

- `agentic_system/*.ps1` (PowerShell 스크립트)
- `agentic_system/*.sh` (Shell 스크립트)
- `agentic_system/*.bat` (배치 파일)
- `ChatGarment/scripts/*.sh`
- `GarmentCodeRC/*.sh`

### ✅ 7. 라이센스 파일

- `ChatGarment/LICENSE`
- `GarmentCodeRC/LICENSE`
- 루트 레벨에 `LICENSE` 파일이 있다면 포함

### ✅ 8. 설정 템플릿 파일

- `GarmentCodeRC/system.template.json`

---

## ❌ 업로드 제외 파일 (GitHub에 업로드하지 않음)

### 🚫 1. 모델 체크포인트 및 가중치 파일

- `checkpoints/` (전체 디렉토리)
  - `checkpoints/llava-v1.5-7b/`
  - `checkpoints/try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final/`
- `model/InternVL2_8B/`
  - `*.safetensors`, `*.bin`, `*.pt` (모델 가중치 파일)
  - `*.json` (모델 설정 파일은 포함 가능, 가중치 파일만 제외)
- `ChatGarment/llava/model/pytorch_model.bin` (모델 파일)

**참고**: 모델 파일은 일반적으로 수 GB~수십 GB 크기이므로 GitHub에 업로드하지 않습니다. 대신 Hugging Face나 별도 저장소에 업로드하고 README에 링크를 제공하세요.

### 🚫 2. 출력 및 생성 파일

- `outputs/` (전체 디렉토리)
  - `outputs/patterns/`
  - `outputs/3d_models/`
  - `outputs/renders/`
  - `outputs/test_*/`
- `ChatGarment/outputs/`
- `uploads/` (전체 디렉토리)
  - 사용자가 업로드한 이미지 파일들

### 🚫 3. 캐시 및 빌드 파일

- `__pycache__/` (모든 디렉토리)
- `*.pyc`
- `*.pyo`
- `*.egg-info/`
- `dist/`
- `build/`
- `.pytest_cache/`
- `.mypy_cache/`

### 🚫 4. 로그 파일

- `*.log`
- `*.log.*`
- `*.jsonl` (로그 파일인 경우)
- `test_output.txt`
- `api_server_log.txt`
- `browser_test_result_*.json` (테스트 결과 파일)

### 🚫 5. 의존성 패키지

- `agentic_system/frontend/node_modules/` (전체 디렉토리)
- `.venv/`, `venv/`, `env/` (가상환경 디렉토리)

### 🚫 6. IDE 및 에디터 설정

- `.vscode/` (일부 프로젝트는 포함하지만, 개인 설정은 제외)
- `.idea/`
- `*.code-workspace`
- `*.swp`
- `.DS_Store`

### 🚫 7. 임시 및 테스트 결과 파일

- `test_3d_fix_response.json`
- `test_response.json`
- `browser_test_result_*.json`
- `GNU nano 7.2.txt`
- `python scriptsevaluate_garment_v2_i.txt`

### 🚫 8. 환경 설정 파일 (민감 정보 포함 가능)

- `.env` (환경 변수 파일, 민감 정보 포함 가능)
- `.env.local`
- `.env.*.local`

### 🚫 9. 컴파일된 바이너리 파일

- `GarmentCodeRC/pygarment/*.dll` (Windows DLL 파일)
- `*.so` (리눅스 공유 라이브러리)
- `*.dylib` (macOS 동적 라이브러리)

### 🚫 10. 기타 제외 파일

- `ChatGarment/assets/` (ChatGarment의 .gitignore에 따라 제외)
- `ChatGarment/runs/` (실행 결과)
- `ChatGarment/uploads/` (사용자 업로드 파일)

---

## 📝 .gitignore 파일 권장 내용

프로젝트 루트에 `.gitignore` 파일을 생성하고 다음 내용을 포함하세요:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/

# 가상환경
venv/
env/
.venv/
ENV/

# 모델 체크포인트 및 가중치
checkpoints/
model/*/pytorch_model.bin
model/*/model.safetensors
model/*/*.safetensors
model/*/*.bin
*.pt
*.pth
*.ckpt

# 출력 및 업로드 파일
outputs/
uploads/
ChatGarment/outputs/
ChatGarment/uploads/
ChatGarment/runs/

# 로그 파일
*.log
*.log.*
*.jsonl
test_output.txt
api_server_log.txt
browser_test_result_*.json

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.code-workspace
*.swp
.DS_Store

# 환경 변수
.env
.env.local
.env.*.local

# 임시 파일
*.tmp
*.temp
GNU nano *.txt
*_test_result_*.json
test_*_response.json

# 컴파일된 바이너리
*.dll
*.so
*.dylib

# ChatGarment 제외 항목
ChatGarment/assets/
ChatGarment/playground/

# GarmentCodeRC 제외 항목
GarmentCodeRC/Logs*/
GarmentCodeRC/output*
GarmentCodeRC/try_imgs/
GarmentCodeRC/try_imgs2/
GarmentCodeRC/summaryfolder/
```

---

## 📦 업로드 전 체크리스트

업로드하기 전에 다음 사항을 확인하세요:

- [ ] `.gitignore` 파일이 프로젝트 루트에 생성되어 있는가?
- [ ] 모델 체크포인트 파일이 제외되어 있는가? (크기 확인)
- [ ] `node_modules/` 디렉토리가 제외되어 있는가?
- [ ] `__pycache__/` 디렉토리가 제외되어 있는가?
- [ ] 로그 파일이 제외되어 있는가?
- [ ] 민감한 정보가 포함된 파일이 없는가? (API 키, 비밀번호 등)
- [ ] README.md 파일이 각 주요 디렉토리에 있는가?
- [ ] 라이센스 파일이 포함되어 있는가?

---

## 🔗 모델 파일 참고

모델 파일은 GitHub에 직접 업로드하지 않고 다음 방법을 사용하세요:

1. **Hugging Face Hub**: 모델 파일을 Hugging Face에 업로드
2. **Google Drive / Dropbox**: 대용량 파일을 클라우드에 업로드
3. **Git LFS**: Git Large File Storage 사용 (큰 파일의 경우)
4. **README에 링크**: 모델 다운로드 링크를 README에 명시

예시:
```markdown
## 모델 다운로드

모델 파일은 다음 링크에서 다운로드할 수 있습니다:
- ChatGarment 모델: [링크]
- InternVL2-8B 모델: [링크]
```

---

## 📊 예상 저장소 크기

- **소스 코드만**: 약 50-100 MB
- **예제 데이터 포함**: 약 200-500 MB
- **모델 파일 포함 (권장하지 않음)**: 수십 GB

**권장**: 모델 파일은 별도로 관리하고, 코드와 문서만 GitHub에 업로드하세요.

