# Extensions Tool 3D 의상 파일 생성
_Exported on 12/15/2025 at 15:48:34 GMT+9 from Cursor (2.2.20)_

---

**User**

담당 도구: Extensions Tool (클래스명: Extensions_2D_to_3D)

연동 방식 (유연성): Integration Switch를 통해 두 가지 방식 중 선택 가능

로컬 통합 (Local Integration): 내부 함수로 직접 실행

마이크로 서비스 호출: 외부 API(Port: 9000)로 원격 호출

처리 과정: 2D 패턴 데이터(JSON)를 입력받아 GarmentCodeRC 모듈이 시뮬레이션을 수행하고, 최종 **3D 의상 파일(.obj)**을 생성 및 반환

---

**Cursor**


코드베이스 구조를 파악하고 `Extensions_2D_to_3D` 클래스 위치를 확인 중입니다.



현재 구현 확인 중입니다. 요구사항에 맞게 Integration Switch를 추가하겠습니다.



`run_garmentcode_sim.py`의 실제 구현 확인 중입니다. 이후 Integration Switch를 추가하겠습니다.



Integration Switch를 추가하고 `_convert_to_3d`를 수정해 로컬 통합과 마이크로 서비스 호출을 모두 지원하도록 업데이트 중입니다.



마이크로서비스의 3D 변환 엔드포인트 확인 중입니다.



요구사항에 맞게 구현 중입니다. 먼저 마이크로서비스에 3D 변환 전용 엔드포인트를 추가하고, `Extensions2DTo3D` 클래스에 Integration Switch를 추가합니다.



마이크로서비스에 3D 변환 엔드포인트 추가 중. 이후 `Extensions2DTo3D` 클래스를 수정합니다.


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGarment 마이크로서비스
리눅스 환경에서 독립적으로 실행
"""

import sys
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import subprocess
import json

# ChatGarment 경로 추가 (자동 감지)
# Windows 또는 Linux 경로 자동 감지
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # agentic_system/chatgarment_service -> agentic_system -> ChatGarment

# 가능한 경로들 시도
possible_paths = [
    project_root / "ChatGarment",
    project_root.parent / "ChatGarment",
    Path.home() / "ChatGarment",  # 홈 디렉토리 기준
]

chatgarment_root = None
for path in possible_paths:
    if path.exists():
        chatgarment_root = path
        print(f"[ChatGarment Service] ChatGarment 경로 발견: {chatgarment_root}")
        sys.path.insert(0, str(chatgarment_root))
        # 작업 디렉토리를 ChatGarment로 변경 (상대 경로 문제 해결)
        os.chdir(str(chatgarment_root))
        print(f"[ChatGarment Service] 작업 디렉토리 변경: {os.getcwd()}")
        break

if chatgarment_root is None:
    print("[ChatGarment Service] 경고: ChatGarment 경로를 찾을 수 없습니다. Mock 모드로 동작합니다.")

app = FastAPI(
    title="ChatGarment Service API",
    description="ChatGarment 마이크로서비스 - 2D to 3D 변환",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChatGarment Pipeline 인스턴스
chatgarment_pipeline = None

def load_chatgarment_pipeline():
    """ChatGarment Pipeline 로딩 (실패 시 Mock 모드)"""
    global chatgarment_pipeline
    
    if chatgarment_pipeline is not None:
        return chatgarment_pipeline
    
    # ChatGarment 경로가 없으면 Mock 모드
    if chatgarment_root is None:
        print("[ChatGarment Service] Mock 모드로 동작합니다 (경로 없음)")
        chatgarment_pipeline = "mock"
        return chatgarment_pipeline
    
    try:
        # 실제 Pipeline 로딩 시도
        # 체크포인트 경로: 프로젝트 루트 기준으로 찾기
        # 가능한 경로들 시도
        possible_checkpoint_paths = [
            project_root / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final" / "pytorch_model.bin",
            project_root.parent / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final" / "pytorch_model.bin",
        ]
        if chatgarment_root:
            possible_checkpoint_paths.append(
                chatgarment_root / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final" / "pytorch_model.bin"
            )
        
        checkpoint_path = None
        for cp_path in possible_checkpoint_paths:
            if cp_path.exists():
                checkpoint_path = cp_path
                print(f"[ChatGarment Service] 체크포인트 발견: {checkpoint_path}")
                break
        
        if checkpoint_path is None:
            print(f"[ChatGarment Service] 체크포인트를 찾을 수 없습니다.")
            print(f"    시도한 경로들:")
            for cp_path in possible_checkpoint_paths:
                print(f"      - {cp_path} (존재: {cp_path.exists()})")
            print("[ChatGarment Service] Mock 모드로 동작합니다")
            chatgarment_pipeline = "mock"
            return chatgarment_pipeline
        
        # 임포트 경로 수정
        sys.path.insert(0, str(project_root / "agentic_system"))
        from agentic_system.tools.chatgarment_integration import ChatGarmentPipeline
        
        # CUDA 사용 가능 여부 확인
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
        except Exception as e:
            print(f"경고: torch 임포트 실패: {e}")
            device = "cpu"
        
        pipeline = ChatGarmentPipeline(
            checkpoint_path=str(checkpoint_path),
            device=device
        )
        
        chatgarment_pipeline = pipeline
        print("✅ ChatGarment Pipeline 로딩 완료")
        return pipeline
        
    except Exception as e:
        print(f"❌ ChatGarment Pipeline 로딩 실패: {str(e)}")
        print("[ChatGarment Service] Mock 모드로 전환합니다")
        import traceback
        traceback.print_exc()
        chatgarment_pipeline = "mock"
        return chatgarment_pipeline

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "chatgarment"}

@app.post("/api/v1/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    text: Optional[str] = Form(None)
):
    """
    이미지 분석
    
    Args:
        image: 업로드된 이미지 파일
        text: 선택적 텍스트 설명
        
    Returns:
        분석 결과 (JSON)
    """
    try:
        # ChatGarment 경로 확인
        if chatgarment_root is None:
            raise HTTPException(
                status_code=500, 
                detail="ChatGarment 경로를 찾을 수 없습니다. Mock 모드를 사용하세요."
            )
        
        # 이미지 저장
        upload_dir = chatgarment_root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 처리
        if image.filename is None:
            image.filename = f"{uuid.uuid4()}.jpg"
        image_path = upload_dir / image.filename
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        # Pipeline 로딩
        pipeline = load_chatgarment_pipeline()
        
        # Mock 모드 처리
        if pipeline == "mock":
            return JSONResponse(content={
                "status": "success",
                "analysis": {
                    "garment_type": "상의",
                    "style": "캐주얼",
                    "color": "검정색",
                    "type": "hoodie"
                },
                "message": "이미지 분석이 완료되었습니다. (Mock 모드)"
            })
        
        # 실제 Pipeline 사용
        result = pipeline.analyze_image(str(image_path), text)
        
        return JSONResponse(content={
            "status": "success",
            "analysis": result,
            "message": "이미지 분석이 완료되었습니다."
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/process")
async def process_image(
    image: UploadFile = File(...),
    text: Optional[str] = Form(None),
    output_dir: Optional[str] = Form(None)
):
    """
    전체 파이프라인 실행 (이미지 분석 + 3D 생성)
    
    Args:
        image: 업로드된 이미지 파일
        text: 선택적 텍스트 설명
        output_dir: 출력 디렉토리 (선택사항)
        
    Returns:
        전체 처리 결과
    """
    try:
        # ChatGarment 경로 확인
        if chatgarment_root is None:
            raise HTTPException(
                status_code=500, 
                detail="ChatGarment 경로를 찾을 수 없습니다. Mock 모드를 사용하세요."
            )
        
        # 이미지 저장
        upload_dir = chatgarment_root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 처리
        if image.filename is None:
            import uuid
            image.filename = f"{uuid.uuid4()}.jpg"
        image_path = upload_dir / image.filename
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = chatgarment_root / "outputs" / "chatgarment"
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Pipeline 로딩
        pipeline = load_chatgarment_pipeline()
        
        # Mock 모드 처리
        if pipeline == "mock":
            # Mock 결과 생성 (기존 extensions.py의 Mock 로직과 유사)
            return JSONResponse(content={
                "status": "success",
                "result": {
                    "status": "success",
                    "analysis": {
                        "garment_type": "상의",
                        "style": "캐주얼",
                        "color": "검정색",
                        "type": "hoodie"
                    },
                    "pattern_path": str(output_dir / "pattern.json"),
                    "mesh_path": str(output_dir / "garment.obj"),
                    "render_path": str(output_dir / "garment_render.png"),
                    "message": "전체 파이프라인이 완료되었습니다. (Mock 모드)"
                },
                "message": "처리가 완료되었습니다. (Mock 모드)"
            })
        
        # 실제 Pipeline 사용
        result = pipeline.process_image(
            str(image_path),
            output_dir=str(output_dir),
            text_description=text
        )
        
        return JSONResponse(content={
            "status": "success",
            "result": result,
            "message": "처리가 완료되었습니다."
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 Pipeline 로드 시도"""
    print("=" * 60)
    print("[ChatGarment Service] 서비스 시작 이벤트")
    print("=" * 60)
    
    # Pipeline 로딩 시도
    print("[ChatGarment Service] Pipeline 로딩 시도...")
    pipeline = load_chatgarment_pipeline()
    
    if pipeline == "mock":
        print("[ChatGarment Service] ⚠️ Mock 모드로 동작합니다")
        print("[ChatGarment Service] 실제 모델을 사용하려면:")
        print("[ChatGarment Service] 1. 체크포인트 경로 확인")
        print("[ChatGarment Service] 2. 모든 의존성 설치 확인")
        print("[ChatGarment Service] 3. 서비스 로그 확인")
    else:
        print("[ChatGarment Service] ✅ 실제 ChatGarment Pipeline이 로드되었습니다!")
    
    print("=" * 60)
    print()

if __name__ == "__main__":
    # ChatGarment 경로 확인
    if chatgarment_root:
        print(f"[ChatGarment Service] ChatGarment 경로: {chatgarment_root}")
        print(f"[ChatGarment Service] 경로 존재 여부: {chatgarment_root.exists()}")
        print(f"[ChatGarment Service] 작업 디렉토리: {os.getcwd()}")
    else:
        print("[ChatGarment Service] ChatGarment 경로를 찾을 수 없습니다. Mock 모드로 동작합니다.")
    
    print("[ChatGarment Service] 서비스 시작: http://0.0.0.0:9000")
    print("[ChatGarment Service] 헬스 체크: http://localhost:9000/health")
    print()
    print("[ChatGarment Service] 서비스가 시작되면 Pipeline 로딩을 시도합니다...")
    print("=" * 60)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )


```

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGarment 마이크로서비스
리눅스 환경에서 독립적으로 실행
"""

import sys
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import subprocess
import json

# ChatGarment 경로 추가 (자동 감지)
# Windows 또는 Linux 경로 자동 감지
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # agentic_system/chatgarment_service -> agentic_system -> ChatGarment

# 가능한 경로들 시도
possible_paths = [
    project_root / "ChatGarment",
    project_root.parent / "ChatGarment",
    Path.home() / "ChatGarment",  # 홈 디렉토리 기준
]

chatgarment_root = None
for path in possible_paths:
    if path.exists():
        chatgarment_root = path
        print(f"[ChatGarment Service] ChatGarment 경로 발견: {chatgarment_root}")
        sys.path.insert(0, str(chatgarment_root))
        # 작업 디렉토리를 ChatGarment로 변경 (상대 경로 문제 해결)
        os.chdir(str(chatgarment_root))
        print(f"[ChatGarment Service] 작업 디렉토리 변경: {os.getcwd()}")
        break

if chatgarment_root is None:
    print("[ChatGarment Service] 경고: ChatGarment 경로를 찾을 수 없습니다. Mock 모드로 동작합니다.")

app = FastAPI(
    title="ChatGarment Service API",
    description="ChatGarment 마이크로서비스 - 2D to 3D 변환",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChatGarment Pipeline 인스턴스
chatgarment_pipeline = None

def load_chatgarment_pipeline():
    """ChatGarment Pipeline 로딩 (실패 시 Mock 모드)"""
    global chatgarment_pipeline
    
    if chatgarment_pipeline is not None:
        return chatgarment_pipeline
    
    # ChatGarment 경로가 없으면 Mock 모드
    if chatgarment_root is None:
        print("[ChatGarment Service] Mock 모드로 동작합니다 (경로 없음)")
        chatgarment_pipeline = "mock"
        return chatgarment_pipeline
    
    try:
        # 실제 Pipeline 로딩 시도
        # 체크포인트 경로: 프로젝트 루트 기준으로 찾기
        # 가능한 경로들 시도
        possible_checkpoint_paths = [
            project_root / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final" / "pytorch_model.bin",
            project_root.parent / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final" / "pytorch_model.bin",
        ]
        if chatgarment_root:
            possible_checkpoint_paths.append(
                chatgarment_root / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final" / "pytorch_model.bin"
            )
        
        checkpoint_path = None
        for cp_path in possible_checkpoint_paths:
            if cp_path.exists():
                checkpoint_path = cp_path
                print(f"[ChatGarment Service] 체크포인트 발견: {checkpoint_path}")
                break
        
        if checkpoint_path is None:
            print(f"[ChatGarment Service] 체크포인트를 찾을 수 없습니다.")
            print(f"    시도한 경로들:")
            for cp_path in possible_checkpoint_paths:
                print(f"      - {cp_path} (존재: {cp_path.exists()})")
            print("[ChatGarment Service] Mock 모드로 동작합니다")
            chatgarment_pipeline = "mock"
            return chatgarment_pipeline
        
        # 임포트 경로 수정
        sys.path.insert(0, str(project_root / "agentic_system"))
        from agentic_system.tools.chatgarment_integration import ChatGarmentPipeline
        
        # CUDA 사용 가능 여부 확인
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
        except Exception as e:
            print(f"경고: torch 임포트 실패: {e}")
            device = "cpu"
        
        pipeline = ChatGarmentPipeline(
            checkpoint_path=str(checkpoint_path),
            device=device
        )
        
        chatgarment_pipeline = pipeline
        print("✅ ChatGarment Pipeline 로딩 완료")
        return pipeline
        
    except Exception as e:
        print(f"❌ ChatGarment Pipeline 로딩 실패: {str(e)}")
        print("[ChatGarment Service] Mock 모드로 전환합니다")
        import traceback
        traceback.print_exc()
        chatgarment_pipeline = "mock"
        return chatgarment_pipeline

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "chatgarment"}

@app.post("/api/v1/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    text: Optional[str] = Form(None)
):
    """
    이미지 분석
    
    Args:
        image: 업로드된 이미지 파일
        text: 선택적 텍스트 설명
        
    Returns:
        분석 결과 (JSON)
    """
    try:
        # ChatGarment 경로 확인
        if chatgarment_root is None:
            raise HTTPException(
                status_code=500, 
                detail="ChatGarment 경로를 찾을 수 없습니다. Mock 모드를 사용하세요."
            )
        
        # 이미지 저장
        upload_dir = chatgarment_root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 처리
        if image.filename is None:
            image.filename = f"{uuid.uuid4()}.jpg"
        image_path = upload_dir / image.filename
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        # Pipeline 로딩
        pipeline = load_chatgarment_pipeline()
        
        # Mock 모드 처리
        if pipeline == "mock":
            return JSONResponse(content={
                "status": "success",
                "analysis": {
                    "garment_type": "상의",
                    "style": "캐주얼",
                    "color": "검정색",
                    "type": "hoodie"
                },
                "message": "이미지 분석이 완료되었습니다. (Mock 모드)"
            })
        
        # 실제 Pipeline 사용
        result = pipeline.analyze_image(str(image_path), text)
        
        return JSONResponse(content={
            "status": "success",
            "analysis": result,
            "message": "이미지 분석이 완료되었습니다."
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/process")
async def process_image(
    image: UploadFile = File(...),
    text: Optional[str] = Form(None),
    output_dir: Optional[str] = Form(None)
):
    """
    전체 파이프라인 실행 (이미지 분석 + 3D 생성)
    
    Args:
        image: 업로드된 이미지 파일
        text: 선택적 텍스트 설명
        output_dir: 출력 디렉토리 (선택사항)
        
    Returns:
        전체 처리 결과
    """
    try:
        # ChatGarment 경로 확인
        if chatgarment_root is None:
            raise HTTPException(
                status_code=500, 
                detail="ChatGarment 경로를 찾을 수 없습니다. Mock 모드를 사용하세요."
            )
        
        # 이미지 저장
        upload_dir = chatgarment_root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 처리
        if image.filename is None:
            import uuid
            image.filename = f"{uuid.uuid4()}.jpg"
        image_path = upload_dir / image.filename
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = chatgarment_root / "outputs" / "chatgarment"
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Pipeline 로딩
        pipeline = load_chatgarment_pipeline()
        
        # Mock 모드 처리
        if pipeline == "mock":
            # Mock 결과 생성 (기존 extensions.py의 Mock 로직과 유사)
            return JSONResponse(content={
                "status": "success",
                "result": {
                    "status": "success",
                    "analysis": {
                        "garment_type": "상의",
                        "style": "캐주얼",
                        "color": "검정색",
                        "type": "hoodie"
                    },
                    "pattern_path": str(output_dir / "pattern.json"),
                    "mesh_path": str(output_dir / "garment.obj"),
                    "render_path": str(output_dir / "garment_render.png"),
                    "message": "전체 파이프라인이 완료되었습니다. (Mock 모드)"
                },
                "message": "처리가 완료되었습니다. (Mock 모드)"
            })
        
        # 실제 Pipeline 사용
        result = pipeline.process_image(
            str(image_path),
            output_dir=str(output_dir),
            text_description=text
        )
        
        return JSONResponse(content={
            "status": "success",
            "result": result,
            "message": "처리가 완료되었습니다."
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class ConvertTo3DRequest(BaseModel):
    """3D 변환 요청 모델"""
    pattern_json_path: str
    output_dir: Optional[str] = None

@app.post("/api/v1/convert_to_3d")
async def convert_to_3d(request: ConvertTo3DRequest):
    """
    2D 패턴 JSON을 3D 모델(.obj)로 변환
    
    Args:
        request: ConvertTo3DRequest 모델
            - pattern_json_path: 2D 패턴 JSON 파일 경로
            - output_dir: 출력 디렉토리 (선택사항)
        
    Returns:
        3D 변환 결과 (mesh_path 포함)
    """
    try:
        # ChatGarment 경로 확인
        if chatgarment_root is None:
            raise HTTPException(
                status_code=500,
                detail="ChatGarment 경로를 찾을 수 없습니다."
            )
        
        pattern_json_path = Path(request.pattern_json_path)
        
        # 패턴 파일 존재 확인
        if not pattern_json_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"패턴 파일을 찾을 수 없습니다: {pattern_json_path}"
            )
        
        # 출력 디렉토리 설정
        if request.output_dir:
            output_dir = Path(request.output_dir)
        else:
            # 패턴 파일과 같은 디렉토리 사용
            output_dir = pattern_json_path.parent
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # GarmentCodeRC 시뮬레이션 실행
        sim_script = chatgarment_root / "run_garmentcode_sim.py"
        
        if not sim_script.exists():
            raise HTTPException(
                status_code=500,
                detail=f"시뮬레이션 스크립트를 찾을 수 없습니다: {sim_script}"
            )
        
        print(f"[ChatGarment Service] 3D 변환 시작: {pattern_json_path}")
        print(f"[ChatGarment Service] 출력 디렉토리: {output_dir}")
        
        # 서브프로세스로 시뮬레이션 실행
        command = [
            "python",
            str(sim_script),
            "--json_spec_file",
            str(pattern_json_path)
        ]
        
        result = subprocess.run(
            command,
            cwd=str(chatgarment_root),
            capture_output=True,
            text=True,
            timeout=600  # 10분 타임아웃
        )
        
        if result.returncode != 0:
            error_msg = result.stderr[:500] if result.stderr else "알 수 없는 오류"
            raise HTTPException(
                status_code=500,
                detail=f"3D 변환 실패: {error_msg}"
            )
        
        # 생성된 3D 모델 파일 찾기
        pattern_dir = pattern_json_path.parent
        garment_name = pattern_json_path.stem.replace("_specification", "")
        mesh_path = pattern_dir / f"{garment_name}_sim.obj"
        
        # 다른 가능한 경로들도 확인
        if not mesh_path.exists():
            # 다른 이름 패턴 시도
            possible_names = [
                pattern_dir / f"{garment_name}.obj",
                pattern_dir / f"{pattern_dir.name}_sim.obj",
                output_dir / f"{garment_name}_sim.obj",
            ]
            for possible_path in possible_names:
                if possible_path.exists():
                    mesh_path = possible_path
                    break
        
        if not mesh_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"3D 모델 파일을 찾을 수 없습니다. 생성된 파일을 확인하세요: {pattern_dir}"
            )
        
        print(f"[ChatGarment Service] 3D 변환 완료: {mesh_path}")
        
        return JSONResponse(content={
            "status": "success",
            "mesh_path": str(mesh_path),
            "mesh_info": {
                "format": "obj",
                "path": str(mesh_path),
                "size_bytes": mesh_path.stat().st_size if mesh_path.exists() else 0
            },
            "message": "3D 변환이 완료되었습니다."
        })
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="3D 변환 타임아웃 (10분 초과)"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"3D 변환 오류: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 Pipeline 로드 시도"""
    print("=" * 60)
    print("[ChatGarment Service] 서비스 시작 이벤트")
    print("=" * 60)
    
    # Pipeline 로딩 시도
    print("[ChatGarment Service] Pipeline 로딩 시도...")
    pipeline = load_chatgarment_pipeline()
    
    if pipeline == "mock":
        print("[ChatGarment Service] ⚠️ Mock 모드로 동작합니다")
        print("[ChatGarment Service] 실제 모델을 사용하려면:")
        print("[ChatGarment Service] 1. 체크포인트 경로 확인")
        print("[ChatGarment Service] 2. 모든 의존성 설치 확인")
        print("[ChatGarment Service] 3. 서비스 로그 확인")
    else:
        print("[ChatGarment Service] ✅ 실제 ChatGarment Pipeline이 로드되었습니다!")
    
    print("=" * 60)
    print()

if __name__ == "__main__":
    # ChatGarment 경로 확인
    if chatgarment_root:
        print(f"[ChatGarment Service] ChatGarment 경로: {chatgarment_root}")
        print(f"[ChatGarment Service] 경로 존재 여부: {chatgarment_root.exists()}")
        print(f"[ChatGarment Service] 작업 디렉토리: {os.getcwd()}")
    else:
        print("[ChatGarment Service] ChatGarment 경로를 찾을 수 없습니다. Mock 모드로 동작합니다.")
    
    print("[ChatGarment Service] 서비스 시작: http://0.0.0.0:9000")
    print("[ChatGarment Service] 헬스 체크: http://localhost:9000/health")
    print()
    print("[ChatGarment Service] 서비스가 시작되면 Pipeline 로딩을 시도합니다...")
    print("=" * 60)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )


```


`extensions_service.py`에 3D 변환 클라이언트 메서드 추가 중. 이후 `Extensions2DTo3D` 클래스를 수정합니다.


```python
"""
ChatGarment 마이크로서비스 클라이언트
Windows 백엔드에서 리눅스 서버의 ChatGarment 서비스 호출
"""

import requests
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수에서 서비스 URL 가져오기
CHATGARMENT_SERVICE_URL = os.getenv(
    "CHATGARMENT_SERVICE_URL",
    "http://localhost:9000"  # 기본값 (로컬 테스트용)
)

class ChatGarmentServiceClient:
    """ChatGarment 마이크로서비스 클라이언트"""
    
    def __init__(self, service_url: Optional[str] = None):
        self.service_url = service_url or CHATGARMENT_SERVICE_URL
        self.base_url = f"{self.service_url}/api/v1"
    
    def health_check(self) -> bool:
        """서비스 헬스 체크"""
        try:
            response = requests.get(f"{self.service_url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def analyze_image(self, image_path: str, text: Optional[str] = None) -> Dict[str, Any]:
        """
        이미지 분석
        
        Args:
            image_path: 이미지 파일 경로
            text: 선택적 텍스트 설명
            
        Returns:
            분석 결과
        """
        try:
            with open(image_path, "rb") as f:
                files = {"image": f}
                data = {}
                if text:
                    data["text"] = text
                
                response = requests.post(
                    f"{self.base_url}/analyze",
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "status": "error",
                        "error": f"서비스 오류: {response.status_code}",
                        "message": response.text
                    }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "서비스 타임아웃",
                "message": "ChatGarment 서비스 응답 시간 초과"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "서비스 연결 오류"
            }
    
    def convert_to_3d(
        self,
        pattern_json_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        2D 패턴 JSON을 3D 모델(.obj)로 변환
        
        Args:
            pattern_json_path: 2D 패턴 JSON 파일 경로
            output_dir: 출력 디렉토리 (선택사항)
            
        Returns:
            3D 변환 결과
        """
        try:
            data = {
                "pattern_json_path": pattern_json_path
            }
            if output_dir:
                data["output_dir"] = output_dir
            
            response = requests.post(
                f"{self.base_url}/convert_to_3d",
                json=data,
                timeout=600  # 10분 타임아웃 (3D 생성 시간 고려)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"서비스 오류: {response.status_code}",
                    "message": response.text
                }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "서비스 타임아웃",
                "message": "ChatGarment 서비스 응답 시간 초과 (10분)"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "서비스 연결 오류"
            }
    
    def process_image(
        self,
        image_path: str,
        text: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        전체 파이프라인 실행 (이미지 분석 + 3D 생성)
        
        Args:
            image_path: 이미지 파일 경로
            text: 선택적 텍스트 설명
            output_dir: 출력 디렉토리 (선택사항)
            
        Returns:
            전체 처리 결과
        """
        try:
            with open(image_path, "rb") as f:
                files = {"image": f}
                data = {}
                if text:
                    data["text"] = text
                if output_dir:
                    data["output_dir"] = output_dir
                
                response = requests.post(
                    f"{self.base_url}/process",
                    files=files,
                    data=data,
                    timeout=300  # 5분 타임아웃 (3D 생성 시간 고려)
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "status": "error",
                        "error": f"서비스 오류: {response.status_code}",
                        "message": response.text
                    }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "서비스 타임아웃",
                "message": "ChatGarment 서비스 응답 시간 초과 (5분)"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "서비스 연결 오류"
            }

def chatgarment_service_tool(action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ChatGarment 마이크로서비스 도구
    
    Args:
        action: 실행할 액션 (analyze, process)
        parameters: 액션에 필요한 파라미터
        context: 실행 컨텍스트
        
    Returns:
        실행 결과
    """
    # 환경 변수 확인
    service_url = os.getenv("CHATGARMENT_SERVICE_URL", "http://localhost:9000")
    logger.info(f"[ChatGarmentServiceTool] 서비스 URL: {service_url}")
    
    client = ChatGarmentServiceClient(service_url=service_url)
    
    # 서비스 헬스 체크
    logger.info(f"[ChatGarmentServiceTool] 헬스 체크 시작: {service_url}/health")
    if not client.health_check():
        logger.error(f"[ChatGarmentServiceTool] 헬스 체크 실패")
        return {
            "status": "error",
            "error": "ChatGarment 서비스에 연결할 수 없습니다",
            "message": f"서비스 URL: {client.service_url}",
            "suggestion": "리눅스 서버에서 ChatGarment 서비스가 실행 중인지 확인하세요."
        }
    
    logger.info(f"[ChatGarmentServiceTool] 헬스 체크 성공")
    
    image_path = parameters.get("image_path") or context.get("image_path")
    logger.info(f"[ChatGarmentServiceTool] 이미지 경로: {image_path}")
    if not image_path:
        logger.error(f"[ChatGarmentServiceTool] 이미지 경로가 없습니다")
        return {
            "status": "error",
            "error": "이미지 경로가 필요합니다"
        }
    
    if not Path(image_path).exists():
        logger.error(f"[ChatGarmentServiceTool] 이미지 파일이 없습니다: {image_path}")
        return {
            "status": "error",
            "error": f"이미지 파일을 찾을 수 없습니다: {image_path}"
        }
    
    text = parameters.get("text_description") or context.get("text")
    logger.info(f"[ChatGarmentServiceTool] 액션: {action}, 텍스트: {text}")
    
    if action == "analyze":
        logger.info(f"[ChatGarmentServiceTool] 이미지 분석 시작...")
        result = client.analyze_image(image_path, text)
        logger.info(f"[ChatGarmentServiceTool] 이미지 분석 결과: status={result.get('status')}")
        return result
    
    elif action == "process":
        output_dir = parameters.get("output_dir") or context.get("output_dir")
        logger.info(f"[ChatGarmentServiceTool] 전체 파이프라인 처리 시작...")
        result = client.process_image(image_path, text, output_dir)
        logger.info(f"[ChatGarmentServiceTool] 전체 파이프라인 처리 결과: status={result.get('status')}")
        return result
    
    else:
        logger.error(f"[ChatGarmentServiceTool] 지원하지 않는 액션: {action}")
        return {
            "status": "error",
            "error": f"지원하지 않는 액션: {action}"
        }

```

```python
"""
ChatGarment 마이크로서비스 클라이언트
Windows 백엔드에서 리눅스 서버의 ChatGarment 서비스 호출
"""

import requests
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수에서 서비스 URL 가져오기
CHATGARMENT_SERVICE_URL = os.getenv(
    "CHATGARMENT_SERVICE_URL",
    "http://localhost:9000"  # 기본값 (로컬 테스트용)
)

class ChatGarmentServiceClient:
    """ChatGarment 마이크로서비스 클라이언트"""
    
    def __init__(self, service_url: Optional[str] = None):
        self.service_url = service_url or CHATGARMENT_SERVICE_URL
        self.base_url = f"{self.service_url}/api/v1"
    
    def health_check(self) -> bool:
        """서비스 헬스 체크"""
        try:
            response = requests.get(f"{self.service_url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def analyze_image(self, image_path: str, text: Optional[str] = None) -> Dict[str, Any]:
        """
        이미지 분석
        
        Args:
            image_path: 이미지 파일 경로
            text: 선택적 텍스트 설명
            
        Returns:
            분석 결과
        """
        try:
            with open(image_path, "rb") as f:
                files = {"image": f}
                data = {}
                if text:
                    data["text"] = text
                
                response = requests.post(
                    f"{self.base_url}/analyze",
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "status": "error",
                        "error": f"서비스 오류: {response.status_code}",
                        "message": response.text
                    }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "서비스 타임아웃",
                "message": "ChatGarment 서비스 응답 시간 초과"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "서비스 연결 오류"
            }
    
    def convert_to_3d(
        self,
        pattern_json_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        2D 패턴 JSON을 3D 모델(.obj)로 변환
        
        Args:
            pattern_json_path: 2D 패턴 JSON 파일 경로
            output_dir: 출력 디렉토리 (선택사항)
            
        Returns:
            3D 변환 결과
        """
        try:
            data = {
                "pattern_json_path": pattern_json_path
            }
            if output_dir:
                data["output_dir"] = output_dir
            
            response = requests.post(
                f"{self.base_url}/convert_to_3d",
                json=data,
                timeout=600  # 10분 타임아웃 (3D 생성 시간 고려)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"서비스 오류: {response.status_code}",
                    "message": response.text
                }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "서비스 타임아웃",
                "message": "ChatGarment 서비스 응답 시간 초과 (10분)"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "서비스 연결 오류"
            }
    
    def process_image(
        self,
        image_path: str,
        text: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        전체 파이프라인 실행 (이미지 분석 + 3D 생성)
        
        Args:
            image_path: 이미지 파일 경로
            text: 선택적 텍스트 설명
            output_dir: 출력 디렉토리 (선택사항)
            
        Returns:
            전체 처리 결과
        """
        try:
            with open(image_path, "rb") as f:
                files = {"image": f}
                data = {}
                if text:
                    data["text"] = text
                if output_dir:
                    data["output_dir"] = output_dir
                
                response = requests.post(
                    f"{self.base_url}/process",
                    files=files,
                    data=data,
                    timeout=300  # 5분 타임아웃 (3D 생성 시간 고려)
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "status": "error",
                        "error": f"서비스 오류: {response.status_code}",
                        "message": response.text
                    }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "서비스 타임아웃",
                "message": "ChatGarment 서비스 응답 시간 초과 (5분)"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "서비스 연결 오류"
            }

def chatgarment_service_tool(action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ChatGarment 마이크로서비스 도구
    
    Args:
        action: 실행할 액션 (analyze, process)
        parameters: 액션에 필요한 파라미터
        context: 실행 컨텍스트
        
    Returns:
        실행 결과
    """
    # 환경 변수 확인
    service_url = os.getenv("CHATGARMENT_SERVICE_URL", "http://localhost:9000")
    logger.info(f"[ChatGarmentServiceTool] 서비스 URL: {service_url}")
    
    client = ChatGarmentServiceClient(service_url=service_url)
    
    # 서비스 헬스 체크
    logger.info(f"[ChatGarmentServiceTool] 헬스 체크 시작: {service_url}/health")
    if not client.health_check():
        logger.error(f"[ChatGarmentServiceTool] 헬스 체크 실패")
        return {
            "status": "error",
            "error": "ChatGarment 서비스에 연결할 수 없습니다",
            "message": f"서비스 URL: {client.service_url}",
            "suggestion": "리눅스 서버에서 ChatGarment 서비스가 실행 중인지 확인하세요."
        }
    
    logger.info(f"[ChatGarmentServiceTool] 헬스 체크 성공")
    
    image_path = parameters.get("image_path") or context.get("image_path")
    logger.info(f"[ChatGarmentServiceTool] 이미지 경로: {image_path}")
    if not image_path:
        logger.error(f"[ChatGarmentServiceTool] 이미지 경로가 없습니다")
        return {
            "status": "error",
            "error": "이미지 경로가 필요합니다"
        }
    
    if not Path(image_path).exists():
        logger.error(f"[ChatGarmentServiceTool] 이미지 파일이 없습니다: {image_path}")
        return {
            "status": "error",
            "error": f"이미지 파일을 찾을 수 없습니다: {image_path}"
        }
    
    text = parameters.get("text_description") or context.get("text")
    logger.info(f"[ChatGarmentServiceTool] 액션: {action}, 텍스트: {text}")
    
    if action == "analyze":
        logger.info(f"[ChatGarmentServiceTool] 이미지 분석 시작...")
        result = client.analyze_image(image_path, text)
        logger.info(f"[ChatGarmentServiceTool] 이미지 분석 결과: status={result.get('status')}")
        return result
    
    elif action == "convert_to_3d":
        pattern_json_path = parameters.get("pattern_json_path")
        if not pattern_json_path:
            logger.error(f"[ChatGarmentServiceTool] 패턴 JSON 경로가 없습니다")
            return {
                "status": "error",
                "error": "패턴 JSON 경로가 필요합니다"
            }
        
        if not Path(pattern_json_path).exists():
            logger.error(f"[ChatGarmentServiceTool] 패턴 파일이 없습니다: {pattern_json_path}")
            return {
                "status": "error",
                "error": f"패턴 파일을 찾을 수 없습니다: {pattern_json_path}"
            }
        
        output_dir = parameters.get("output_dir") or context.get("output_dir")
        logger.info(f"[ChatGarmentServiceTool] 3D 변환 시작...")
        result = client.convert_to_3d(pattern_json_path, output_dir)
        logger.info(f"[ChatGarmentServiceTool] 3D 변환 결과: status={result.get('status')}")
        return result
    
    elif action == "process":
        output_dir = parameters.get("output_dir") or context.get("output_dir")
        logger.info(f"[ChatGarmentServiceTool] 전체 파이프라인 처리 시작...")
        result = client.process_image(image_path, text, output_dir)
        logger.info(f"[ChatGarmentServiceTool] 전체 파이프라인 처리 결과: status={result.get('status')}")
        return result
    
    else:
        logger.error(f"[ChatGarmentServiceTool] 지원하지 않는 액션: {action}")
        return {
            "status": "error",
            "error": f"지원하지 않는 액션: {action}"
        }

```


`Extensions2DTo3D` 클래스에 Integration Switch 추가 및 `_convert_to_3d` 메서드 수정 중.


```python
"""
Extensions Tool - 2D to 3D 변환 도구

실제 ChatGarment 시스템과 통합하여 2D 이미지를 3D 모델로 변환
"""

from typing import Dict, Any, Optional
import os
import sys
from pathlib import Path
import json
import subprocess
import torch
import random

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ChatGarment"))

# transformers는 항상 임포트 (모델 로딩에 필요)
try:
    import transformers
except ImportError:
    transformers = None

# ChatGarment 임포트
try:
    from .chatgarment_integration import ChatGarmentPipeline
    CHATGARMENT_AVAILABLE = True
except ImportError as e:
    print(f"ChatGarment 통합 모듈 임포트 경고: {e}")
    try:
        from llava.garment_utils_v2 import (
            try_generate_garments,
            run_garmentcode_parser_float50,
            recursive_change_params
        )
        from llava.json_fixer import repair_json
        from llava.model import *
        from llava.mm_utils import tokenizer_image_token
        from llava import conversation as conversation_lib
        from llava.constants import DEFAULT_IMAGE_TOKEN
        if transformers is None:
            import transformers
        CHATGARMENT_AVAILABLE = True
        CHATGARMENT_PIPELINE_AVAILABLE = False
    except ImportError as e2:
        print(f"ChatGarment 임포트 경고: {e2}")
        CHATGARMENT_AVAILABLE = False
        CHATGARMENT_PIPELINE_AVAILABLE = False
    else:
        CHATGARMENT_PIPELINE_AVAILABLE = False
else:
    CHATGARMENT_PIPELINE_AVAILABLE = True


class Extensions2DTo3D:
    """
    Extensions Tool - 2D to 3D 변환
    
    실제 ChatGarment 모델을 사용하여 2D 이미지를 3D 모델로 변환
    
    Integration Switch를 통해 두 가지 통합 방식 중 선택 가능:
    - Local Integration: 내부 함수로 직접 실행 (로컬 통합)
    - Microservice: 외부 API(Port: 9000)로 원격 호출 (마이크로 서비스)
    """
    
    def __init__(self, integration_mode: str = "local"):
        """
        Args:
            integration_mode: 통합 방식 선택
                - "local": 로컬 통합 (내부 함수로 직접 실행)
                - "microservice": 마이크로 서비스 호출 (외부 API, Port: 9000)
        """
        self.name = "extensions_2d_to_3d"
        self.chatgarment_path = project_root / "ChatGarment"
        self.checkpoint_path = project_root / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final"
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_loaded = False
        
        # Integration Switch 설정
        # 환경 변수로도 제어 가능: EXTENSIONS_INTEGRATION_MODE (local 또는 microservice)
        env_mode = os.getenv("EXTENSIONS_INTEGRATION_MODE", "").lower()
        if env_mode in ["local", "microservice"]:
            self.integration_mode = env_mode
            print(f"[Extensions2DTo3D] 환경 변수에서 통합 방식 설정: {self.integration_mode}")
        elif integration_mode in ["local", "microservice"]:
            self.integration_mode = integration_mode
            print(f"[Extensions2DTo3D] 통합 방식 설정: {self.integration_mode}")
        else:
            self.integration_mode = "local"  # 기본값: 로컬 통합
            print(f"[Extensions2DTo3D] 기본 통합 방식 사용: {self.integration_mode}")
        
        # 마이크로 서비스 클라이언트 초기화 (필요 시)
        self.service_client = None
        if self.integration_mode == "microservice":
            try:
                from .extensions_service import ChatGarmentServiceClient
                service_url = os.getenv("CHATGARMENT_SERVICE_URL", "http://localhost:9000")
                self.service_client = ChatGarmentServiceClient(service_url=service_url)
                print(f"[Extensions2DTo3D] 마이크로 서비스 클라이언트 초기화: {service_url}")
            except Exception as e:
                print(f"⚠️ 마이크로 서비스 클라이언트 초기화 실패: {e}")
                print("   로컬 통합 모드로 전환합니다.")
                self.integration_mode = "local"
                self.service_client = None
        
        # 실제 ChatGarment 파이프라인 사용 여부 (로컬 모드에서만 필요)
        self.chatgarment_pipeline = None
        if self.integration_mode == "local" and CHATGARMENT_PIPELINE_AVAILABLE:
            try:
                self.chatgarment_pipeline = ChatGarmentPipeline(device=self.device)
                print("✅ ChatGarment 실제 파이프라인 사용 가능")
            except Exception as e:
                print(f"⚠️ ChatGarment 파이프라인 초기화 실패: {e}")
                self.chatgarment_pipeline = None
        
    def _load_model(self):
        """ChatGarment 모델 로딩 (지연 로딩)"""
        if self.model_loaded or not CHATGARMENT_AVAILABLE:
            return
        
        # ChatGarmentPipeline 사용 (deepspeed 오류 회피)
        if self.chatgarment_pipeline:
            try:
                print("=" * 60)
                print("ChatGarment 모델 로딩 시작 (Pipeline 사용)...")
                print("=" * 60)
                
                # Pipeline을 통한 모델 로딩
                self.chatgarment_pipeline.load_model()
                
                if self.chatgarment_pipeline.model_loaded:
                    # Pipeline의 모델과 토크나이저 사용
                    self.model = self.chatgarment_pipeline.model
                    self.tokenizer = self.chatgarment_pipeline.tokenizer
                    self.image_processor = getattr(self.chatgarment_pipeline, 'image_processor', None)
                    self.model_loaded = True
                    
                    print("=" * 60)
                    print("✅ ChatGarment 모델 로딩 완료! (Pipeline 사용)")
                    print(f"   모델 디바이스: {self.model.device if hasattr(self.model, 'device') else 'N/A'}")
                    print("=" * 60)
                    return
                else:
                    print("❌ ChatGarmentPipeline 모델 로딩 실패")
                    print("   Pipeline의 model_loaded가 False입니다.")
            except Exception as e:
                print("=" * 60)
                print(f"❌ ChatGarmentPipeline 오류")
                print("=" * 60)
                print(f"오류 메시지: {str(e)}")
                print(f"오류 타입: {type(e).__name__}")
                import traceback
                print("\n상세 오류 정보:")
                traceback.print_exc()
                print("=" * 60)
        
        # Pipeline 사용 실패 시 직접 로딩 시도 (deepspeed 오류 가능)
        print("\n⚠️ Pipeline 사용 실패, 직접 모델 로딩 시도...")
        
        # transformers 임포트 확인
        if transformers is None:
            print("❌ transformers 모듈을 찾을 수 없습니다.")
            print("   pip install transformers 실행 필요")
            self.model_loaded = False
            return
        
        try:
            print("=" * 60)
            print("ChatGarment 모델 로딩 시작 (직접 로딩)...")
            print("=" * 60)
            
            # 모델 경로 설정 (llava-v1.5-7b 경로 사용)
            model_path = str(project_root / "checkpoints" / "llava-v1.5-7b")
            checkpoint_file = str(self.checkpoint_path / "pytorch_model.bin")
            
            print(f"모델 경로: {model_path}")
            print(f"체크포인트 경로: {checkpoint_file}")
            
            # 모델 경로 검증
            if not os.path.exists(model_path):
                print(f"❌ 모델 경로를 찾을 수 없습니다: {model_path}")
                print("   llava-v1.5-7b 모델이 다운로드되어 있는지 확인하세요.")
                self.model_loaded = False
                return
            
            # config.json 파일 확인
            config_file = os.path.join(model_path, "config.json")
            if not os.path.exists(config_file):
                print(f"❌ config.json 파일을 찾을 수 없습니다: {config_file}")
                print("   모델이 올바르게 다운로드되지 않았을 수 있습니다.")
                self.model_loaded = False
                return
            
            # config.json 읽기 및 검증
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                model_type = config.get('model_type', 'unknown')
                print(f"✅ 모델 타입 확인: {model_type}")
                if model_type != 'llava':
                    print(f"⚠️ 경고: 모델 타입이 'llava'가 아닙니다: {model_type}")
            except Exception as e:
                print(f"⚠️ config.json 읽기 오류: {e}")
            
            # 체크포인트 파일 확인
            if not os.path.exists(checkpoint_file):
                print(f"❌ 체크포인트를 찾을 수 없습니다: {checkpoint_file}")
                print("   ChatGarment 파인튜닝 체크포인트가 필요합니다.")
                self.model_loaded = False
                return
            
            print(f"✅ 모델 경로 검증 완료")
            print(f"✅ 체크포인트 파일 확인 완료")
            
            # deepspeed 더미 모듈 생성 (오류 방지)
            import sys
            import types
            if 'deepspeed' not in sys.modules:
                sys.modules['deepspeed'] = types.SimpleNamespace(__version__='0.0.0')
                print("✅ deepspeed 더미 모듈 생성 완료")
            
            # 토크나이저 로딩
            print("토크나이저 로딩 중...")
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                model_path,
                use_fast=False,
            )
            self.tokenizer.pad_token = self.tokenizer.unk_token
            num_added_tokens = self.tokenizer.add_tokens("[SEG]")
            seg_token_idx = self.tokenizer("[SEG]", add_special_tokens=False).input_ids[-1]
            print(f"✅ 토크나이저 로딩 완료 (SEG 토큰 인덱스: {seg_token_idx})")
            
            # 모델 로딩
            print("모델 아키텍처 로딩 중...")
            from llava.train.train_garmentcode_outfit import ModelArguments
            model_args = ModelArguments(model_name_or_path=model_path)
            
            print("ChatGarment 모델 인스턴스 생성 중...")
            self.model = GarmentGPTFloat50ForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,
                seg_token_idx=seg_token_idx,
            )
            print("✅ 모델 인스턴스 생성 완료")
            
            # 체크포인트 로딩
            print("체크포인트 로딩 중...")
            print(f"  체크포인트 파일: {checkpoint_file}")
            print(f"  파일 크기: {os.path.getsize(checkpoint_file) / (1024**3):.2f} GB")
            
            state_dict = torch.load(checkpoint_file, map_location="cpu")
            print("체크포인트 상태 딕셔너리 로딩 완료")
            
            print("모델 가중치 로딩 중...")
            missing_keys, unexpected_keys = self.model.load_state_dict(state_dict, strict=False)
            if missing_keys:
                print(f"⚠️ 누락된 키: {len(missing_keys)}개 (일부는 정상일 수 있음)")
            if unexpected_keys:
                print(f"⚠️ 예상치 못한 키: {len(unexpected_keys)}개 (LoRA 가중치 등)")
            print("✅ 모델 가중치 로딩 완료")
            
            # 디바이스 설정
            print(f"디바이스 설정 중: {self.device}")
            self.model = self.model.bfloat16().to(self.device).eval()
            print(f"✅ 디바이스 설정 완료: {self.model.device}")
            
            # 대화 템플릿 설정
            try:
                from llava import conversation as conversation_lib
                conversation_lib.default_conversation = conversation_lib.conv_templates["v1"]
                print("✅ 대화 템플릿 설정 완료")
            except Exception as e:
                print(f"⚠️ 대화 템플릿 설정 오류 (무시 가능): {e}")
            
            self.model_loaded = True
            print("=" * 60)
            print("✅ ChatGarment 모델 로딩 완료! (직접 로딩)")
            print("=" * 60)
            
        except Exception as e:
            print("=" * 60)
            print(f"❌ ChatGarment 모델 로딩 실패")
            print("=" * 60)
            print(f"오류 메시지: {str(e)}")
            print(f"오류 타입: {type(e).__name__}")
            import traceback
            print("\n상세 오류 정보:")
            traceback.print_exc()
            print("=" * 60)
            print("⚠️ Mock 모드로 동작합니다.")
            print("   실제 이미지 분석이 수행되지 않으며, Mock 데이터가 생성됩니다.")
            print("=" * 60)
            self.model_loaded = False
    
    def execute(self, action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        도구 실행
        
        Args:
            action: 실행할 액션 (analyze_image, generate_pattern, convert_to_3d, render_result)
            parameters: 액션에 필요한 파라미터
            context: 실행 컨텍스트
            
        Returns:
            Dict: 실행 결과
        """
        print(f"[Extensions2DTo3D] execute 호출: action={action}")
        
        try:
            if action == "analyze_image":
                print("[Extensions2DTo3D] analyze_image 시작...")
                result = self._analyze_image(parameters, context)
                print(f"[Extensions2DTo3D] analyze_image 완료: status={result.get('status')}")
                return result
            elif action == "generate_pattern":
                print("[Extensions2DTo3D] generate_pattern 시작...")
                result = self._generate_pattern(parameters, context)
                print(f"[Extensions2DTo3D] generate_pattern 완료: status={result.get('status')}")
                return result
            elif action == "convert_to_3d":
                print("[Extensions2DTo3D] convert_to_3d 시작...")
                result = self._convert_to_3d(parameters, context)
                print(f"[Extensions2DTo3D] convert_to_3d 완료: status={result.get('status')}")
                return result
            elif action == "render_result":
                print("[Extensions2DTo3D] render_result 시작...")
                result = self._render_result(parameters, context)
                print(f"[Extensions2DTo3D] render_result 완료: status={result.get('status')}")
                return result
            elif action == "process_request":
                print("[Extensions2DTo3D] process_request 시작...")
                result = self._process_full_pipeline(parameters, context)
                print(f"[Extensions2DTo3D] process_request 완료: status={result.get('status')}")
                return result
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            print(f"[Extensions2DTo3D] execute 오류: action={action}, error={str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _analyze_image(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        이미지 분석 (ChatGarment 모델 사용)
        
        실제 ChatGarment 모델로 이미지를 분석하여 의류 정보 추출
        """
        image_path = parameters.get("image_path") or context.get("image_path")
        text_description = parameters.get("text_description") or context.get("text")
        
        if not image_path:
            raise ValueError("이미지 경로가 필요합니다.")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_path}")
        
        # 모델 로딩
        self._load_model()
        
        if not self.model_loaded:
            # Mock 모드
            print("⚠️ 모델이 로드되지 않아 Mock 모드로 동작합니다.")
            return self._mock_analyze_image(image_path, text_description)
        
        # ChatGarmentPipeline 사용 (권장 방법 - 오류 회피)
        if self.chatgarment_pipeline and self.chatgarment_pipeline.model_loaded:
            try:
                print("[Extensions2DTo3D] ChatGarmentPipeline을 사용하여 이미지 분석...")
                # Pipeline의 analyze_image 메서드를 직접 사용 (이미 검증된 방법)
                # 이 메서드는 cache_position 오류를 이미 처리하고 있음
                result = self.chatgarment_pipeline.analyze_image(image_path)
                
                if result and result.get("status") == "success":
                    print("✅ 실제 ChatGarment 모델로 이미지 분석 완료!")
                    return {
                        "status": "success",
                        "analysis": result.get("analysis", {}),
                        "text_output": result.get("text_output", ""),
                        "float_preds": result.get("float_preds"),
                        "image_path": image_path,
                        "message": "이미지 분석이 완료되었습니다. (실제 모델 사용)"
                    }
                else:
                    raise Exception(f"Pipeline 분석 실패: {result}")
            except Exception as e:
                print(f"⚠️ ChatGarmentPipeline 사용 중 오류: {str(e)}")
                print("   직접 모델 사용 방법으로 전환...")
                import traceback
                traceback.print_exc()
        
        try:
            # deepspeed 더미 모듈 생성 (오류 방지)
            import sys
            import types
            if 'deepspeed' not in sys.modules:
                sys.modules['deepspeed'] = types.SimpleNamespace(__version__='0.0.0')
            
            # 이미지 로딩
            from PIL import Image
            image = Image.open(image_path).convert('RGB')
            
            # 이미지 전처리
            # DataArguments 임포트 시 deepspeed 오류 방지를 위해 try-except 사용
            try:
                from llava.train.train_garmentcode_outfit import DataArguments
            except (ImportError, RuntimeError) as e:
                # deepspeed 오류 발생 시 대체 방법 사용
                print(f"⚠️ DataArguments 임포트 오류: {e}")
                print("   대체 방법으로 이미지 프로세서 사용")
                # ChatGarmentPipeline의 image_processor 사용
                if hasattr(self, 'image_processor') and self.image_processor:
                    processor = self.image_processor
                else:
                    # 직접 vision tower에서 가져오기
                    processor = self.model.get_vision_tower().image_processor
                
                # 간단한 DataArguments 대체
                class SimpleDataArgs:
                    def __init__(self):
                        self.image_processor = processor
                        self.image_aspect_ratio = "pad"
                
                data_args = SimpleDataArgs()
            else:
                data_args = DataArguments()
                data_args.image_processor = self.model.get_vision_tower().image_processor
                data_args.image_aspect_ratio = "pad"
            
            processor = data_args.image_processor
            image_clip = processor.preprocess(image, return_tensors='pt')['pixel_values'][0]
            image_clip = image_clip.unsqueeze(0).to(self.device).bfloat16()
            
            # 필요한 모듈 임포트 확인
            if 'conversation_lib' not in globals():
                try:
                    from llava import conversation as conversation_lib
                except ImportError:
                    print("❌ conversation_lib 임포트 실패")
                    raise
            
            if 'DEFAULT_IMAGE_TOKEN' not in globals():
                try:
                    from llava.constants import DEFAULT_IMAGE_TOKEN
                except ImportError:
                    print("❌ DEFAULT_IMAGE_TOKEN 임포트 실패")
                    raise
            
            if 'tokenizer_image_token' not in globals():
                try:
                    from llava.mm_utils import tokenizer_image_token
                except ImportError:
                    print("❌ tokenizer_image_token 임포트 실패")
                    raise
            
            if 'repair_json' not in globals():
                try:
                    from llava.json_fixer import repair_json
                except ImportError:
                    print("❌ repair_json 임포트 실패")
                    raise
            
            # 프롬프트 구성
            question = 'Can you describe the geometry features of the garments worn by the model in the Json format?'
            conv = conversation_lib.conv_templates["v1"].copy()
            conv.messages = []
            prompt = DEFAULT_IMAGE_TOKEN + "\n" + question
            conv.append_message(conv.roles[0], prompt)
            conv.append_message(conv.roles[1], None)
            prompt = conv.get_prompt()
            
            # 토크나이징
            input_ids = tokenizer_image_token(prompt, self.tokenizer, return_tensors="pt")
            input_ids = input_ids.unsqueeze(0).to(self.device)
            
            # 추론
            with torch.no_grad():
                output_ids, float_preds, seg_token_mask = self.model.evaluate(
                    image_clip,
                    image_clip,
                    input_ids,
                    max_new_tokens=2048,
                    tokenizer=self.tokenizer,
                )
            
            # 결과 파싱
            output_ids = output_ids[0, 1:]
            text_output = self.tokenizer.decode(output_ids, skip_special_tokens=False).strip().replace("</s>", "")
            text_output = text_output.replace('[STARTS]', '').replace('[SEG]', '').replace('[ENDS]', '')
            
            # JSON 수정
            json_output = repair_json(text_output, return_objects=True)
            
            return {
                "status": "success",
                "analysis": json_output,
                "text_output": text_output,
                "float_preds": float_preds.cpu().numpy().tolist() if float_preds is not None else None,
                "image_path": image_path,
                "message": "이미지 분석이 완료되었습니다."
            }
            
        except Exception as e:
            print(f"이미지 분석 오류: {str(e)}")
            return self._mock_analyze_image(image_path, text_description)
    
    def _generate_pattern(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        패턴 생성 (GarmentCode 사용)
        
        분석 결과를 기반으로 2D 패턴 생성
        """
        # 이전 단계 결과 사용
        analysis = parameters.get("_dependency_result") or context.get("step_1")
        
        if not analysis:
            raise ValueError("이미지 분석 결과가 필요합니다.")
        
        json_output = analysis.get("analysis") or analysis
        float_preds = analysis.get("float_preds")
        
        # 출력 디렉토리 설정
        output_dir = project_root / "outputs" / "patterns"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        garment_name = "garment_001"
        
        try:
            # 패턴 생성
            all_json_spec_files = []
            saved_dir = str(output_dir)
            
            all_json_spec_files = run_garmentcode_parser_float50(
                all_json_spec_files,
                json_output,
                float_preds,
                saved_dir
            )
            
            # 생성된 파일 경로
            pattern_json_path = os.path.join(saved_dir, f'valid_garment_{garment_name}', 
                                            f'valid_garment_{garment_name}_specification.json')
            
            if os.path.exists(pattern_json_path):
                return {
                    "status": "success",
                    "pattern_path": pattern_json_path,
                    "pattern_info": {
                        "type": json_output.get("type", "unknown"),
                        "components": list(json_output.keys()),
                    },
                    "message": "패턴 생성이 완료되었습니다."
                }
            else:
                # Mock 패턴 생성
                return self._mock_generate_pattern(analysis)
                
        except Exception as e:
            print(f"패턴 생성 오류: {str(e)}")
            return self._mock_generate_pattern(analysis)
    
    def _convert_to_3d(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        3D 모델로 변환 (GarmentCodeRC 사용)
        
        패턴을 3D 메시로 변환
        """
        # 이전 단계 결과 사용
        pattern_result = parameters.get("_dependency_result") or context.get("step_2")
        
        if not pattern_result:
            print("[Extensions2DTo3D] 패턴 생성 결과가 없어 Mock 모드로 전환합니다.")
            return self._mock_convert_to_3d({})
        
        pattern_json_path = pattern_result.get("pattern_path")
        
        # 패턴 파일이 없으면 Mock 모드로 전환
        if not pattern_json_path or not os.path.exists(pattern_json_path):
            print(f"[Extensions2DTo3D] 패턴 파일을 찾을 수 없습니다: {pattern_json_path}")
            print("[Extensions2DTo3D] Mock 모드로 3D 변환을 수행합니다.")
            return self._mock_convert_to_3d(pattern_result)
        
        # 실제 3D 변환 시도 (Mock 모드에서는 건너뛰기)
        # PoC 단계에서는 실제 변환 대신 Mock 변환 사용
        print("[Extensions2DTo3D] 실제 3D 변환 스크립트 확인...")
        sim_script = project_root / "ChatGarment" / "run_garmentcode_sim.py"
        
        # 실제 변환을 시도할지 여부 (현재는 Mock 모드 사용)
        try_real_conversion = False  # PoC 단계에서는 False
        
        if try_real_conversion and sim_script.exists() and os.path.exists(pattern_json_path):
            try:
                print(f"[Extensions2DTo3D] 실제 3D 변환 스크립트 실행: {sim_script}")
                # 서브프로세스로 3D 변환 실행
                command = f'python "{sim_script}" --json_spec_file "{pattern_json_path}"'
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(project_root),
                    timeout=600  # 10분 타임아웃
                )
                
                if result.returncode == 0:
                    # 생성된 3D 모델 경로 찾기
                    pattern_dir = os.path.dirname(pattern_json_path)
                    mesh_path = os.path.join(pattern_dir, f"{os.path.basename(pattern_dir)}_sim.obj")
                    
                    if os.path.exists(mesh_path):
                        print(f"[Extensions2DTo3D] 실제 3D 메시 생성 완료: {mesh_path}")
                        return {
                            "status": "success",
                            "mesh_path": mesh_path,
                            "mesh_info": {
                                "format": "obj",
                                "path": mesh_path
                            },
                            "message": "3D 변환이 완료되었습니다."
                        }
                    else:
                        print(f"[Extensions2DTo3D] 3D 메시 파일을 찾을 수 없습니다: {mesh_path}")
                else:
                    print(f"[Extensions2DTo3D] 3D 변환 스크립트 실패 (종료 코드: {result.returncode})")
                    print(f"[Extensions2DTo3D] STDOUT: {result.stdout[:500]}")
                    print(f"[Extensions2DTo3D] STDERR: {result.stderr[:500]}")
            except subprocess.TimeoutExpired:
                print("[Extensions2DTo3D] 3D 변환 타임아웃 (10분 초과)")
            except Exception as e:
                print(f"[Extensions2DTo3D] 실제 3D 변환 시도 중 오류: {str(e)}")
        
        # Mock 변환으로 전환 (PoC 단계 기본 동작)
        print("[Extensions2DTo3D] Mock 모드로 3D 변환을 수행합니다.")
        return self._mock_convert_to_3d(pattern_result)
    
    def _render_result(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        결과 렌더링
        """
        # 이전 단계 결과 사용
        mesh_result = parameters.get("_dependency_result") or context.get("step_3")
        
        if not mesh_result:
            raise ValueError("3D 모델 결과가 필요합니다.")
        
        mesh_path = mesh_result.get("mesh_path")
        
        # TODO: 실제 렌더링 엔진 사용 (PyTorch3D 등)
        # 현재는 Mock 구현
        render_path = self._mock_render(mesh_result)
        
        return {
            "status": "success",
            "render_path": render_path,
            "visualization": {
                "image_path": render_path,
                "mesh_path": mesh_path
            },
            "message": "렌더링이 완료되었습니다."
        }
    
    def _process_full_pipeline(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        전체 파이프라인 실행
        
        ChatGarment 마이크로서비스 사용 시도, 실패 시 Mock 모드
        """
        # ChatGarment 마이크로서비스 사용 여부 확인
        use_service = os.getenv("USE_CHATGARMENT_SERVICE", "false").lower() == "true"
        
        if use_service:
            print("[Extensions2DTo3D] ChatGarment 마이크로서비스 사용 시도...")
            try:
                from .extensions_service import chatgarment_service_tool
                
                image_path = parameters.get("image_path") or context.get("image_path")
                if image_path and Path(image_path).exists():
                    result = chatgarment_service_tool("process", {
                        "image_path": image_path,
                        "text_description": parameters.get("text_description") or context.get("text"),
                        "output_dir": context.get("output_dir")
                    }, context)
                    
                    if result.get("status") == "success":
                        print("[Extensions2DTo3D] ChatGarment 마이크로서비스 처리 완료")
                        return {
                            "status": "success",
                            "pipeline_complete": True,
                            "result": result.get("result", {}),
                            "message": "전체 파이프라인이 완료되었습니다. (ChatGarment 서비스)"
                        }
                    else:
                        print(f"[Extensions2DTo3D] 서비스 오류: {result.get('error')}")
                        print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
                else:
                    print("[Extensions2DTo3D] 이미지 경로가 없어 서비스를 사용할 수 없습니다.")
                    print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
            except Exception as e:
                print(f"[Extensions2DTo3D] 서비스 연결 실패: {str(e)}")
                print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
                import traceback
                traceback.print_exc()
        
        # Mock 모드 또는 서비스 사용 실패 시 기존 로직 실행
        print("[Extensions2DTo3D] Mock 모드로 전체 파이프라인 실행...")
        step1 = self._analyze_image(parameters, context)
        context["step_1"] = step1
        
        step2 = self._generate_pattern(parameters, context)
        context["step_2"] = step2
        
        step3 = self._convert_to_3d(parameters, context)
        context["step_3"] = step3
        
        step4 = self._render_result(parameters, context)
        
        return {
            "status": "success",
            "pipeline_complete": True,
            "steps": {
                "analysis": step1,
                "pattern": step2,
                "3d_conversion": step3,
                "render": step4
            },
            "final_result": step4,
            "message": "전체 파이프라인이 완료되었습니다. (Mock 모드)"
        }
    
    def _mock_analyze_image(self, image_path: str, text_description: Optional[str]) -> Dict[str, Any]:
        """Mock 이미지 분석"""
        return {
            "status": "success",
            "analysis": {
                "garment_type": "상의",
                "style": "캐주얼",
                "color": "검정색",
                "type": "hoodie"
            },
            "image_path": image_path,
            "message": "이미지 분석이 완료되었습니다. (Mock 모드)"
        }
    
    def _mock_generate_pattern(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Mock 패턴 생성"""
        output_dir = project_root / "outputs" / "patterns"
        output_dir.mkdir(parents=True, exist_ok=True)
        pattern_path = str(output_dir / "pattern.json")
        
        # 실제 패턴 JSON 파일 생성 (Mock 데이터)
        pattern_data = {
            "garment_type": analysis.get("analysis", {}).get("type", "hoodie") if isinstance(analysis.get("analysis"), dict) else "hoodie",
            "components": ["front", "back", "sleeves", "hood"],
            "specification": {
                "front": {
                    "width": 50,
                    "height": 70,
                    "seams": ["shoulder", "side", "bottom"]
                },
                "back": {
                    "width": 50,
                    "height": 70,
                    "seams": ["shoulder", "side", "bottom"]
                },
                "sleeves": {
                    "length": 60,
                    "width": 30,
                    "seams": ["armhole", "side", "cuff"]
                },
                "hood": {
                    "width": 45,
                    "height": 35,
                    "seams": ["crown", "face_opening"]
                }
            },
            "version": "1.0",
            "created_by": "mock_generator"
        }
        
        # 파일 쓰기
        try:
            with open(pattern_path, 'w', encoding='utf-8') as f:
                json.dump(pattern_data, f, ensure_ascii=False, indent=2)
            print(f"[Extensions2DTo3D] Mock 패턴 파일 생성 완료: {pattern_path}")
        except Exception as e:
            print(f"[Extensions2DTo3D] Mock 패턴 파일 생성 실패: {e}")
        
        return {
            "status": "success",
            "pattern_path": pattern_path,
            "pattern_info": {
                "type": pattern_data["garment_type"],
                "components": pattern_data["components"],
            },
            "message": "패턴 생성이 완료되었습니다. (Mock 모드)"
        }
    
    def _mock_convert_to_3d(self, pattern_result: Dict[str, Any]) -> Dict[str, Any]:
        """Mock 3D 변환"""
        output_dir = project_root / "outputs" / "3d_models"
        output_dir.mkdir(parents=True, exist_ok=True)
        mesh_path = str(output_dir / "garment.obj")
        
        # 실제 Mock OBJ 파일 생성 (간단한 3D 메시)
        try:
            with open(mesh_path, 'w', encoding='utf-8') as f:
                # 간단한 Mock OBJ 파일 (큐브 형태)
                f.write("# Mock 3D Garment Mesh\n")
                f.write("# Generated by Mock Converter\n")
                f.write("g garment_mock\n")
                
                # 정점 (vertices) - 간단한 박스 형태
                vertices = [
                    (-1, -1, -1),  # 0
                    (1, -1, -1),   # 1
                    (1, 1, -1),    # 2
                    (-1, 1, -1),   # 3
                    (-1, -1, 1),   # 4
                    (1, -1, 1),    # 5
                    (1, 1, 1),     # 6
                    (-1, 1, 1),    # 7
                ]
                
                for v in vertices:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                
                # 면 (faces) - 박스의 6개 면
                faces = [
                    (0, 1, 2, 3),  # 앞면
                    (4, 7, 6, 5),  # 뒷면
                    (0, 4, 5, 1),  # 아래면
                    (2, 6, 7, 3),  # 위면
                    (0, 3, 7, 4),  # 왼쪽면
                    (1, 5, 6, 2),  # 오른쪽면
                ]
                
                for face in faces:
                    f.write(f"f {' '.join([str(i+1) for i in face])}\n")
            
            print(f"[Extensions2DTo3D] Mock 3D 메시 파일 생성 완료: {mesh_path}")
        except Exception as e:
            print(f"[Extensions2DTo3D] Mock 3D 메시 파일 생성 실패: {e}")
        
        return {
            "status": "success",
            "mesh_path": mesh_path,
            "mesh_info": {
                "vertices": 8,
                "faces": 6,
                "format": "obj"
            },
            "message": "3D 변환이 완료되었습니다. (Mock 모드)"
        }
    
    def _mock_render(self, mesh_result: Dict[str, Any]) -> str:
        """Mock 렌더링"""
        output_dir = project_root / "outputs" / "renders"
        output_dir.mkdir(parents=True, exist_ok=True)
        render_path = str(output_dir / "garment_render.png")
        return render_path


# 도구 함수로 사용하기 위한 래퍼
def extensions_2d_to_3d_tool(action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """도구 함수 래퍼"""
    tool = Extensions2DTo3D()
    return tool.execute(action, parameters, context)

```

```python
"""
Extensions Tool - 2D to 3D 변환 도구

실제 ChatGarment 시스템과 통합하여 2D 이미지를 3D 모델로 변환
"""

from typing import Dict, Any, Optional
import os
import sys
from pathlib import Path
import json
import subprocess
import torch
import random

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ChatGarment"))

# transformers는 항상 임포트 (모델 로딩에 필요)
try:
    import transformers
except ImportError:
    transformers = None

# ChatGarment 임포트
try:
    from .chatgarment_integration import ChatGarmentPipeline
    CHATGARMENT_AVAILABLE = True
except ImportError as e:
    print(f"ChatGarment 통합 모듈 임포트 경고: {e}")
    try:
        from llava.garment_utils_v2 import (
            try_generate_garments,
            run_garmentcode_parser_float50,
            recursive_change_params
        )
        from llava.json_fixer import repair_json
        from llava.model import *
        from llava.mm_utils import tokenizer_image_token
        from llava import conversation as conversation_lib
        from llava.constants import DEFAULT_IMAGE_TOKEN
        if transformers is None:
            import transformers
        CHATGARMENT_AVAILABLE = True
        CHATGARMENT_PIPELINE_AVAILABLE = False
    except ImportError as e2:
        print(f"ChatGarment 임포트 경고: {e2}")
        CHATGARMENT_AVAILABLE = False
        CHATGARMENT_PIPELINE_AVAILABLE = False
    else:
        CHATGARMENT_PIPELINE_AVAILABLE = False
else:
    CHATGARMENT_PIPELINE_AVAILABLE = True


class Extensions2DTo3D:
    """
    Extensions Tool - 2D to 3D 변환
    
    실제 ChatGarment 모델을 사용하여 2D 이미지를 3D 모델로 변환
    
    Integration Switch를 통해 두 가지 통합 방식 중 선택 가능:
    - Local Integration: 내부 함수로 직접 실행 (로컬 통합)
    - Microservice: 외부 API(Port: 9000)로 원격 호출 (마이크로 서비스)
    """
    
    def __init__(self, integration_mode: str = "local"):
        """
        Args:
            integration_mode: 통합 방식 선택
                - "local": 로컬 통합 (내부 함수로 직접 실행)
                - "microservice": 마이크로 서비스 호출 (외부 API, Port: 9000)
        """
        self.name = "extensions_2d_to_3d"
        self.chatgarment_path = project_root / "ChatGarment"
        self.checkpoint_path = project_root / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final"
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_loaded = False
        
        # Integration Switch 설정
        # 환경 변수로도 제어 가능: EXTENSIONS_INTEGRATION_MODE (local 또는 microservice)
        env_mode = os.getenv("EXTENSIONS_INTEGRATION_MODE", "").lower()
        if env_mode in ["local", "microservice"]:
            self.integration_mode = env_mode
            print(f"[Extensions2DTo3D] 환경 변수에서 통합 방식 설정: {self.integration_mode}")
        elif integration_mode in ["local", "microservice"]:
            self.integration_mode = integration_mode
            print(f"[Extensions2DTo3D] 통합 방식 설정: {self.integration_mode}")
        else:
            self.integration_mode = "local"  # 기본값: 로컬 통합
            print(f"[Extensions2DTo3D] 기본 통합 방식 사용: {self.integration_mode}")
        
        # 마이크로 서비스 클라이언트 초기화 (필요 시)
        self.service_client = None
        if self.integration_mode == "microservice":
            try:
                from .extensions_service import ChatGarmentServiceClient
                service_url = os.getenv("CHATGARMENT_SERVICE_URL", "http://localhost:9000")
                self.service_client = ChatGarmentServiceClient(service_url=service_url)
                print(f"[Extensions2DTo3D] 마이크로 서비스 클라이언트 초기화: {service_url}")
            except Exception as e:
                print(f"⚠️ 마이크로 서비스 클라이언트 초기화 실패: {e}")
                print("   로컬 통합 모드로 전환합니다.")
                self.integration_mode = "local"
                self.service_client = None
        
        # 실제 ChatGarment 파이프라인 사용 여부 (로컬 모드에서만 필요)
        self.chatgarment_pipeline = None
        if self.integration_mode == "local" and CHATGARMENT_PIPELINE_AVAILABLE:
            try:
                self.chatgarment_pipeline = ChatGarmentPipeline(device=self.device)
                print("✅ ChatGarment 실제 파이프라인 사용 가능")
            except Exception as e:
                print(f"⚠️ ChatGarment 파이프라인 초기화 실패: {e}")
                self.chatgarment_pipeline = None
        
    def _load_model(self):
        """ChatGarment 모델 로딩 (지연 로딩)"""
        if self.model_loaded or not CHATGARMENT_AVAILABLE:
            return
        
        # ChatGarmentPipeline 사용 (deepspeed 오류 회피)
        if self.chatgarment_pipeline:
            try:
                print("=" * 60)
                print("ChatGarment 모델 로딩 시작 (Pipeline 사용)...")
                print("=" * 60)
                
                # Pipeline을 통한 모델 로딩
                self.chatgarment_pipeline.load_model()
                
                if self.chatgarment_pipeline.model_loaded:
                    # Pipeline의 모델과 토크나이저 사용
                    self.model = self.chatgarment_pipeline.model
                    self.tokenizer = self.chatgarment_pipeline.tokenizer
                    self.image_processor = getattr(self.chatgarment_pipeline, 'image_processor', None)
                    self.model_loaded = True
                    
                    print("=" * 60)
                    print("✅ ChatGarment 모델 로딩 완료! (Pipeline 사용)")
                    print(f"   모델 디바이스: {self.model.device if hasattr(self.model, 'device') else 'N/A'}")
                    print("=" * 60)
                    return
                else:
                    print("❌ ChatGarmentPipeline 모델 로딩 실패")
                    print("   Pipeline의 model_loaded가 False입니다.")
            except Exception as e:
                print("=" * 60)
                print(f"❌ ChatGarmentPipeline 오류")
                print("=" * 60)
                print(f"오류 메시지: {str(e)}")
                print(f"오류 타입: {type(e).__name__}")
                import traceback
                print("\n상세 오류 정보:")
                traceback.print_exc()
                print("=" * 60)
        
        # Pipeline 사용 실패 시 직접 로딩 시도 (deepspeed 오류 가능)
        print("\n⚠️ Pipeline 사용 실패, 직접 모델 로딩 시도...")
        
        # transformers 임포트 확인
        if transformers is None:
            print("❌ transformers 모듈을 찾을 수 없습니다.")
            print("   pip install transformers 실행 필요")
            self.model_loaded = False
            return
        
        try:
            print("=" * 60)
            print("ChatGarment 모델 로딩 시작 (직접 로딩)...")
            print("=" * 60)
            
            # 모델 경로 설정 (llava-v1.5-7b 경로 사용)
            model_path = str(project_root / "checkpoints" / "llava-v1.5-7b")
            checkpoint_file = str(self.checkpoint_path / "pytorch_model.bin")
            
            print(f"모델 경로: {model_path}")
            print(f"체크포인트 경로: {checkpoint_file}")
            
            # 모델 경로 검증
            if not os.path.exists(model_path):
                print(f"❌ 모델 경로를 찾을 수 없습니다: {model_path}")
                print("   llava-v1.5-7b 모델이 다운로드되어 있는지 확인하세요.")
                self.model_loaded = False
                return
            
            # config.json 파일 확인
            config_file = os.path.join(model_path, "config.json")
            if not os.path.exists(config_file):
                print(f"❌ config.json 파일을 찾을 수 없습니다: {config_file}")
                print("   모델이 올바르게 다운로드되지 않았을 수 있습니다.")
                self.model_loaded = False
                return
            
            # config.json 읽기 및 검증
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                model_type = config.get('model_type', 'unknown')
                print(f"✅ 모델 타입 확인: {model_type}")
                if model_type != 'llava':
                    print(f"⚠️ 경고: 모델 타입이 'llava'가 아닙니다: {model_type}")
            except Exception as e:
                print(f"⚠️ config.json 읽기 오류: {e}")
            
            # 체크포인트 파일 확인
            if not os.path.exists(checkpoint_file):
                print(f"❌ 체크포인트를 찾을 수 없습니다: {checkpoint_file}")
                print("   ChatGarment 파인튜닝 체크포인트가 필요합니다.")
                self.model_loaded = False
                return
            
            print(f"✅ 모델 경로 검증 완료")
            print(f"✅ 체크포인트 파일 확인 완료")
            
            # deepspeed 더미 모듈 생성 (오류 방지)
            import sys
            import types
            if 'deepspeed' not in sys.modules:
                sys.modules['deepspeed'] = types.SimpleNamespace(__version__='0.0.0')
                print("✅ deepspeed 더미 모듈 생성 완료")
            
            # 토크나이저 로딩
            print("토크나이저 로딩 중...")
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                model_path,
                use_fast=False,
            )
            self.tokenizer.pad_token = self.tokenizer.unk_token
            num_added_tokens = self.tokenizer.add_tokens("[SEG]")
            seg_token_idx = self.tokenizer("[SEG]", add_special_tokens=False).input_ids[-1]
            print(f"✅ 토크나이저 로딩 완료 (SEG 토큰 인덱스: {seg_token_idx})")
            
            # 모델 로딩
            print("모델 아키텍처 로딩 중...")
            from llava.train.train_garmentcode_outfit import ModelArguments
            model_args = ModelArguments(model_name_or_path=model_path)
            
            print("ChatGarment 모델 인스턴스 생성 중...")
            self.model = GarmentGPTFloat50ForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,
                seg_token_idx=seg_token_idx,
            )
            print("✅ 모델 인스턴스 생성 완료")
            
            # 체크포인트 로딩
            print("체크포인트 로딩 중...")
            print(f"  체크포인트 파일: {checkpoint_file}")
            print(f"  파일 크기: {os.path.getsize(checkpoint_file) / (1024**3):.2f} GB")
            
            state_dict = torch.load(checkpoint_file, map_location="cpu")
            print("체크포인트 상태 딕셔너리 로딩 완료")
            
            print("모델 가중치 로딩 중...")
            missing_keys, unexpected_keys = self.model.load_state_dict(state_dict, strict=False)
            if missing_keys:
                print(f"⚠️ 누락된 키: {len(missing_keys)}개 (일부는 정상일 수 있음)")
            if unexpected_keys:
                print(f"⚠️ 예상치 못한 키: {len(unexpected_keys)}개 (LoRA 가중치 등)")
            print("✅ 모델 가중치 로딩 완료")
            
            # 디바이스 설정
            print(f"디바이스 설정 중: {self.device}")
            self.model = self.model.bfloat16().to(self.device).eval()
            print(f"✅ 디바이스 설정 완료: {self.model.device}")
            
            # 대화 템플릿 설정
            try:
                from llava import conversation as conversation_lib
                conversation_lib.default_conversation = conversation_lib.conv_templates["v1"]
                print("✅ 대화 템플릿 설정 완료")
            except Exception as e:
                print(f"⚠️ 대화 템플릿 설정 오류 (무시 가능): {e}")
            
            self.model_loaded = True
            print("=" * 60)
            print("✅ ChatGarment 모델 로딩 완료! (직접 로딩)")
            print("=" * 60)
            
        except Exception as e:
            print("=" * 60)
            print(f"❌ ChatGarment 모델 로딩 실패")
            print("=" * 60)
            print(f"오류 메시지: {str(e)}")
            print(f"오류 타입: {type(e).__name__}")
            import traceback
            print("\n상세 오류 정보:")
            traceback.print_exc()
            print("=" * 60)
            print("⚠️ Mock 모드로 동작합니다.")
            print("   실제 이미지 분석이 수행되지 않으며, Mock 데이터가 생성됩니다.")
            print("=" * 60)
            self.model_loaded = False
    
    def execute(self, action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        도구 실행
        
        Args:
            action: 실행할 액션 (analyze_image, generate_pattern, convert_to_3d, render_result)
            parameters: 액션에 필요한 파라미터
            context: 실행 컨텍스트
            
        Returns:
            Dict: 실행 결과
        """
        print(f"[Extensions2DTo3D] execute 호출: action={action}")
        
        try:
            if action == "analyze_image":
                print("[Extensions2DTo3D] analyze_image 시작...")
                result = self._analyze_image(parameters, context)
                print(f"[Extensions2DTo3D] analyze_image 완료: status={result.get('status')}")
                return result
            elif action == "generate_pattern":
                print("[Extensions2DTo3D] generate_pattern 시작...")
                result = self._generate_pattern(parameters, context)
                print(f"[Extensions2DTo3D] generate_pattern 완료: status={result.get('status')}")
                return result
            elif action == "convert_to_3d":
                print("[Extensions2DTo3D] convert_to_3d 시작...")
                result = self._convert_to_3d(parameters, context)
                print(f"[Extensions2DTo3D] convert_to_3d 완료: status={result.get('status')}")
                return result
            elif action == "render_result":
                print("[Extensions2DTo3D] render_result 시작...")
                result = self._render_result(parameters, context)
                print(f"[Extensions2DTo3D] render_result 완료: status={result.get('status')}")
                return result
            elif action == "process_request":
                print("[Extensions2DTo3D] process_request 시작...")
                result = self._process_full_pipeline(parameters, context)
                print(f"[Extensions2DTo3D] process_request 완료: status={result.get('status')}")
                return result
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            print(f"[Extensions2DTo3D] execute 오류: action={action}, error={str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _analyze_image(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        이미지 분석 (ChatGarment 모델 사용)
        
        실제 ChatGarment 모델로 이미지를 분석하여 의류 정보 추출
        """
        image_path = parameters.get("image_path") or context.get("image_path")
        text_description = parameters.get("text_description") or context.get("text")
        
        if not image_path:
            raise ValueError("이미지 경로가 필요합니다.")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_path}")
        
        # 모델 로딩
        self._load_model()
        
        if not self.model_loaded:
            # Mock 모드
            print("⚠️ 모델이 로드되지 않아 Mock 모드로 동작합니다.")
            return self._mock_analyze_image(image_path, text_description)
        
        # ChatGarmentPipeline 사용 (권장 방법 - 오류 회피)
        if self.chatgarment_pipeline and self.chatgarment_pipeline.model_loaded:
            try:
                print("[Extensions2DTo3D] ChatGarmentPipeline을 사용하여 이미지 분석...")
                # Pipeline의 analyze_image 메서드를 직접 사용 (이미 검증된 방법)
                # 이 메서드는 cache_position 오류를 이미 처리하고 있음
                result = self.chatgarment_pipeline.analyze_image(image_path)
                
                if result and result.get("status") == "success":
                    print("✅ 실제 ChatGarment 모델로 이미지 분석 완료!")
                    return {
                        "status": "success",
                        "analysis": result.get("analysis", {}),
                        "text_output": result.get("text_output", ""),
                        "float_preds": result.get("float_preds"),
                        "image_path": image_path,
                        "message": "이미지 분석이 완료되었습니다. (실제 모델 사용)"
                    }
                else:
                    raise Exception(f"Pipeline 분석 실패: {result}")
            except Exception as e:
                print(f"⚠️ ChatGarmentPipeline 사용 중 오류: {str(e)}")
                print("   직접 모델 사용 방법으로 전환...")
                import traceback
                traceback.print_exc()
        
        try:
            # deepspeed 더미 모듈 생성 (오류 방지)
            import sys
            import types
            if 'deepspeed' not in sys.modules:
                sys.modules['deepspeed'] = types.SimpleNamespace(__version__='0.0.0')
            
            # 이미지 로딩
            from PIL import Image
            image = Image.open(image_path).convert('RGB')
            
            # 이미지 전처리
            # DataArguments 임포트 시 deepspeed 오류 방지를 위해 try-except 사용
            try:
                from llava.train.train_garmentcode_outfit import DataArguments
            except (ImportError, RuntimeError) as e:
                # deepspeed 오류 발생 시 대체 방법 사용
                print(f"⚠️ DataArguments 임포트 오류: {e}")
                print("   대체 방법으로 이미지 프로세서 사용")
                # ChatGarmentPipeline의 image_processor 사용
                if hasattr(self, 'image_processor') and self.image_processor:
                    processor = self.image_processor
                else:
                    # 직접 vision tower에서 가져오기
                    processor = self.model.get_vision_tower().image_processor
                
                # 간단한 DataArguments 대체
                class SimpleDataArgs:
                    def __init__(self):
                        self.image_processor = processor
                        self.image_aspect_ratio = "pad"
                
                data_args = SimpleDataArgs()
            else:
                data_args = DataArguments()
                data_args.image_processor = self.model.get_vision_tower().image_processor
                data_args.image_aspect_ratio = "pad"
            
            processor = data_args.image_processor
            image_clip = processor.preprocess(image, return_tensors='pt')['pixel_values'][0]
            image_clip = image_clip.unsqueeze(0).to(self.device).bfloat16()
            
            # 필요한 모듈 임포트 확인
            if 'conversation_lib' not in globals():
                try:
                    from llava import conversation as conversation_lib
                except ImportError:
                    print("❌ conversation_lib 임포트 실패")
                    raise
            
            if 'DEFAULT_IMAGE_TOKEN' not in globals():
                try:
                    from llava.constants import DEFAULT_IMAGE_TOKEN
                except ImportError:
                    print("❌ DEFAULT_IMAGE_TOKEN 임포트 실패")
                    raise
            
            if 'tokenizer_image_token' not in globals():
                try:
                    from llava.mm_utils import tokenizer_image_token
                except ImportError:
                    print("❌ tokenizer_image_token 임포트 실패")
                    raise
            
            if 'repair_json' not in globals():
                try:
                    from llava.json_fixer import repair_json
                except ImportError:
                    print("❌ repair_json 임포트 실패")
                    raise
            
            # 프롬프트 구성
            question = 'Can you describe the geometry features of the garments worn by the model in the Json format?'
            conv = conversation_lib.conv_templates["v1"].copy()
            conv.messages = []
            prompt = DEFAULT_IMAGE_TOKEN + "\n" + question
            conv.append_message(conv.roles[0], prompt)
            conv.append_message(conv.roles[1], None)
            prompt = conv.get_prompt()
            
            # 토크나이징
            input_ids = tokenizer_image_token(prompt, self.tokenizer, return_tensors="pt")
            input_ids = input_ids.unsqueeze(0).to(self.device)
            
            # 추론
            with torch.no_grad():
                output_ids, float_preds, seg_token_mask = self.model.evaluate(
                    image_clip,
                    image_clip,
                    input_ids,
                    max_new_tokens=2048,
                    tokenizer=self.tokenizer,
                )
            
            # 결과 파싱
            output_ids = output_ids[0, 1:]
            text_output = self.tokenizer.decode(output_ids, skip_special_tokens=False).strip().replace("</s>", "")
            text_output = text_output.replace('[STARTS]', '').replace('[SEG]', '').replace('[ENDS]', '')
            
            # JSON 수정
            json_output = repair_json(text_output, return_objects=True)
            
            return {
                "status": "success",
                "analysis": json_output,
                "text_output": text_output,
                "float_preds": float_preds.cpu().numpy().tolist() if float_preds is not None else None,
                "image_path": image_path,
                "message": "이미지 분석이 완료되었습니다."
            }
            
        except Exception as e:
            print(f"이미지 분석 오류: {str(e)}")
            return self._mock_analyze_image(image_path, text_description)
    
    def _generate_pattern(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        패턴 생성 (GarmentCode 사용)
        
        분석 결과를 기반으로 2D 패턴 생성
        """
        # 이전 단계 결과 사용
        analysis = parameters.get("_dependency_result") or context.get("step_1")
        
        if not analysis:
            raise ValueError("이미지 분석 결과가 필요합니다.")
        
        json_output = analysis.get("analysis") or analysis
        float_preds = analysis.get("float_preds")
        
        # 출력 디렉토리 설정
        output_dir = project_root / "outputs" / "patterns"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        garment_name = "garment_001"
        
        try:
            # 패턴 생성
            all_json_spec_files = []
            saved_dir = str(output_dir)
            
            all_json_spec_files = run_garmentcode_parser_float50(
                all_json_spec_files,
                json_output,
                float_preds,
                saved_dir
            )
            
            # 생성된 파일 경로
            pattern_json_path = os.path.join(saved_dir, f'valid_garment_{garment_name}', 
                                            f'valid_garment_{garment_name}_specification.json')
            
            if os.path.exists(pattern_json_path):
                return {
                    "status": "success",
                    "pattern_path": pattern_json_path,
                    "pattern_info": {
                        "type": json_output.get("type", "unknown"),
                        "components": list(json_output.keys()),
                    },
                    "message": "패턴 생성이 완료되었습니다."
                }
            else:
                # Mock 패턴 생성
                return self._mock_generate_pattern(analysis)
                
        except Exception as e:
            print(f"패턴 생성 오류: {str(e)}")
            return self._mock_generate_pattern(analysis)
    
    def _convert_to_3d(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        3D 모델로 변환 (GarmentCodeRC 사용)
        
        2D 패턴 데이터(JSON)를 입력받아 GarmentCodeRC 모듈이 시뮬레이션을 수행하고,
        최종 3D 의상 파일(.obj)을 생성 및 반환
        
        Integration Switch에 따라 두 가지 방식 중 선택:
        - Local Integration: 내부 함수로 직접 실행
        - Microservice: 외부 API(Port: 9000)로 원격 호출
        """
        # 이전 단계 결과 사용
        pattern_result = parameters.get("_dependency_result") or context.get("step_2")
        
        if not pattern_result:
            print("[Extensions2DTo3D] 패턴 생성 결과가 없어 Mock 모드로 전환합니다.")
            return self._mock_convert_to_3d({})
        
        pattern_json_path = pattern_result.get("pattern_path")
        
        # 패턴 파일이 없으면 Mock 모드로 전환
        if not pattern_json_path or not os.path.exists(pattern_json_path):
            print(f"[Extensions2DTo3D] 패턴 파일을 찾을 수 없습니다: {pattern_json_path}")
            print("[Extensions2DTo3D] Mock 모드로 3D 변환을 수행합니다.")
            return self._mock_convert_to_3d(pattern_result)
        
        # Integration Switch에 따라 처리 방식 선택
        if self.integration_mode == "microservice":
            return self._convert_to_3d_microservice(pattern_json_path, parameters, context)
        else:
            return self._convert_to_3d_local(pattern_json_path, parameters, context)
    
    def _convert_to_3d_local(self, pattern_json_path: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        로컬 통합 방식: 내부 함수로 직접 실행
        
        GarmentCodeRC 모듈을 사용하여 2D 패턴 JSON을 3D 모델(.obj)로 변환
        """
        print(f"[Extensions2DTo3D] 로컬 통합 모드로 3D 변환 시작: {pattern_json_path}")
        
        # GarmentCodeRC 시뮬레이션 스크립트 확인
        sim_script = project_root / "ChatGarment" / "run_garmentcode_sim.py"
        
        if not sim_script.exists():
            print(f"[Extensions2DTo3D] 시뮬레이션 스크립트를 찾을 수 없습니다: {sim_script}")
            print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
            return self._mock_convert_to_3d({"pattern_path": pattern_json_path})
        
        try:
            print(f"[Extensions2DTo3D] GarmentCodeRC 시뮬레이션 실행: {sim_script}")
            
            # 서브프로세스로 3D 변환 실행
            command = [
                "python",
                str(sim_script),
                "--json_spec_file",
                str(pattern_json_path)
            ]
            
            result = subprocess.run(
                command,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=600  # 10분 타임아웃
            )
            
            if result.returncode == 0:
                # 생성된 3D 모델 경로 찾기
                pattern_dir = os.path.dirname(pattern_json_path)
                garment_name = os.path.basename(pattern_json_path).replace("_specification.json", "")
                
                # 가능한 메시 파일 경로들 확인
                possible_mesh_paths = [
                    os.path.join(pattern_dir, f"{garment_name}_sim.obj"),
                    os.path.join(pattern_dir, f"{os.path.basename(pattern_dir)}_sim.obj"),
                    os.path.join(pattern_dir, f"{garment_name}.obj"),
                ]
                
                mesh_path = None
                for possible_path in possible_mesh_paths:
                    if os.path.exists(possible_path):
                        mesh_path = possible_path
                        break
                
                if mesh_path:
                    print(f"[Extensions2DTo3D] ✅ 3D 메시 생성 완료: {mesh_path}")
                    return {
                        "status": "success",
                        "mesh_path": mesh_path,
                        "mesh_info": {
                            "format": "obj",
                            "path": mesh_path,
                            "size_bytes": os.path.getsize(mesh_path) if os.path.exists(mesh_path) else 0
                        },
                        "integration_mode": "local",
                        "message": "3D 변환이 완료되었습니다. (로컬 통합)"
                    }
                else:
                    print(f"[Extensions2DTo3D] 3D 메시 파일을 찾을 수 없습니다.")
                    print(f"    확인한 경로들: {possible_mesh_paths}")
                    print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
                    return self._mock_convert_to_3d({"pattern_path": pattern_json_path})
            else:
                print(f"[Extensions2DTo3D] 3D 변환 스크립트 실패 (종료 코드: {result.returncode})")
                print(f"[Extensions2DTo3D] STDOUT: {result.stdout[:500]}")
                print(f"[Extensions2DTo3D] STDERR: {result.stderr[:500]}")
                print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
                return self._mock_convert_to_3d({"pattern_path": pattern_json_path})
                
        except subprocess.TimeoutExpired:
            print("[Extensions2DTo3D] 3D 변환 타임아웃 (10분 초과)")
            print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
            return self._mock_convert_to_3d({"pattern_path": pattern_json_path})
        except Exception as e:
            print(f"[Extensions2DTo3D] 로컬 3D 변환 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
            return self._mock_convert_to_3d({"pattern_path": pattern_json_path})
    
    def _convert_to_3d_microservice(self, pattern_json_path: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        마이크로 서비스 호출 방식: 외부 API(Port: 9000)로 원격 호출
        
        ChatGarment 마이크로서비스를 통해 2D 패턴 JSON을 3D 모델(.obj)로 변환
        """
        print(f"[Extensions2DTo3D] 마이크로 서비스 모드로 3D 변환 시작: {pattern_json_path}")
        
        if not self.service_client:
            print("[Extensions2DTo3D] 마이크로 서비스 클라이언트가 없습니다.")
            print("[Extensions2DTo3D] 로컬 통합 모드로 전환합니다.")
            return self._convert_to_3d_local(pattern_json_path, parameters, context)
        
        # 서비스 헬스 체크
        if not self.service_client.health_check():
            print("[Extensions2DTo3D] 마이크로 서비스에 연결할 수 없습니다.")
            print("[Extensions2DTo3D] 로컬 통합 모드로 전환합니다.")
            return self._convert_to_3d_local(pattern_json_path, parameters, context)
        
        try:
            # 출력 디렉토리 설정
            output_dir = parameters.get("output_dir") or context.get("output_dir")
            
            # 마이크로 서비스 호출
            result = self.service_client.convert_to_3d(pattern_json_path, output_dir)
            
            if result.get("status") == "success":
                print(f"[Extensions2DTo3D] ✅ 마이크로 서비스를 통한 3D 변환 완료")
                return {
                    "status": "success",
                    "mesh_path": result.get("mesh_path"),
                    "mesh_info": result.get("mesh_info", {}),
                    "integration_mode": "microservice",
                    "message": "3D 변환이 완료되었습니다. (마이크로 서비스)"
                }
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"[Extensions2DTo3D] 마이크로 서비스 오류: {error_msg}")
                print("[Extensions2DTo3D] 로컬 통합 모드로 전환합니다.")
                return self._convert_to_3d_local(pattern_json_path, parameters, context)
                
        except Exception as e:
            print(f"[Extensions2DTo3D] 마이크로 서비스 호출 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            print("[Extensions2DTo3D] 로컬 통합 모드로 전환합니다.")
            return self._convert_to_3d_local(pattern_json_path, parameters, context)
    
    def _render_result(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        결과 렌더링
        """
        # 이전 단계 결과 사용
        mesh_result = parameters.get("_dependency_result") or context.get("step_3")
        
        if not mesh_result:
            raise ValueError("3D 모델 결과가 필요합니다.")
        
        mesh_path = mesh_result.get("mesh_path")
        
        # TODO: 실제 렌더링 엔진 사용 (PyTorch3D 등)
        # 현재는 Mock 구현
        render_path = self._mock_render(mesh_result)
        
        return {
            "status": "success",
            "render_path": render_path,
            "visualization": {
                "image_path": render_path,
                "mesh_path": mesh_path
            },
            "message": "렌더링이 완료되었습니다."
        }
    
    def _process_full_pipeline(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        전체 파이프라인 실행
        
        ChatGarment 마이크로서비스 사용 시도, 실패 시 Mock 모드
        """
        # ChatGarment 마이크로서비스 사용 여부 확인
        use_service = os.getenv("USE_CHATGARMENT_SERVICE", "false").lower() == "true"
        
        if use_service:
            print("[Extensions2DTo3D] ChatGarment 마이크로서비스 사용 시도...")
            try:
                from .extensions_service import chatgarment_service_tool
                
                image_path = parameters.get("image_path") or context.get("image_path")
                if image_path and Path(image_path).exists():
                    result = chatgarment_service_tool("process", {
                        "image_path": image_path,
                        "text_description": parameters.get("text_description") or context.get("text"),
                        "output_dir": context.get("output_dir")
                    }, context)
                    
                    if result.get("status") == "success":
                        print("[Extensions2DTo3D] ChatGarment 마이크로서비스 처리 완료")
                        return {
                            "status": "success",
                            "pipeline_complete": True,
                            "result": result.get("result", {}),
                            "message": "전체 파이프라인이 완료되었습니다. (ChatGarment 서비스)"
                        }
                    else:
                        print(f"[Extensions2DTo3D] 서비스 오류: {result.get('error')}")
                        print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
                else:
                    print("[Extensions2DTo3D] 이미지 경로가 없어 서비스를 사용할 수 없습니다.")
                    print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
            except Exception as e:
                print(f"[Extensions2DTo3D] 서비스 연결 실패: {str(e)}")
                print("[Extensions2DTo3D] Mock 모드로 전환합니다.")
                import traceback
                traceback.print_exc()
        
        # Mock 모드 또는 서비스 사용 실패 시 기존 로직 실행
        print("[Extensions2DTo3D] Mock 모드로 전체 파이프라인 실행...")
        step1 = self._analyze_image(parameters, context)
        context["step_1"] = step1
        
        step2 = self._generate_pattern(parameters, context)
        context["step_2"] = step2
        
        step3 = self._convert_to_3d(parameters, context)
        context["step_3"] = step3
        
        step4 = self._render_result(parameters, context)
        
        return {
            "status": "success",
            "pipeline_complete": True,
            "steps": {
                "analysis": step1,
                "pattern": step2,
                "3d_conversion": step3,
                "render": step4
            },
            "final_result": step4,
            "message": "전체 파이프라인이 완료되었습니다. (Mock 모드)"
        }
    
    def _mock_analyze_image(self, image_path: str, text_description: Optional[str]) -> Dict[str, Any]:
        """Mock 이미지 분석"""
        return {
            "status": "success",
            "analysis": {
                "garment_type": "상의",
                "style": "캐주얼",
                "color": "검정색",
                "type": "hoodie"
            },
            "image_path": image_path,
            "message": "이미지 분석이 완료되었습니다. (Mock 모드)"
        }
    
    def _mock_generate_pattern(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Mock 패턴 생성"""
        output_dir = project_root / "outputs" / "patterns"
        output_dir.mkdir(parents=True, exist_ok=True)
        pattern_path = str(output_dir / "pattern.json")
        
        # 실제 패턴 JSON 파일 생성 (Mock 데이터)
        pattern_data = {
            "garment_type": analysis.get("analysis", {}).get("type", "hoodie") if isinstance(analysis.get("analysis"), dict) else "hoodie",
            "components": ["front", "back", "sleeves", "hood"],
            "specification": {
                "front": {
                    "width": 50,
                    "height": 70,
                    "seams": ["shoulder", "side", "bottom"]
                },
                "back": {
                    "width": 50,
                    "height": 70,
                    "seams": ["shoulder", "side", "bottom"]
                },
                "sleeves": {
                    "length": 60,
                    "width": 30,
                    "seams": ["armhole", "side", "cuff"]
                },
                "hood": {
                    "width": 45,
                    "height": 35,
                    "seams": ["crown", "face_opening"]
                }
            },
            "version": "1.0",
            "created_by": "mock_generator"
        }
        
        # 파일 쓰기
        try:
            with open(pattern_path, 'w', encoding='utf-8') as f:
                json.dump(pattern_data, f, ensure_ascii=False, indent=2)
            print(f"[Extensions2DTo3D] Mock 패턴 파일 생성 완료: {pattern_path}")
        except Exception as e:
            print(f"[Extensions2DTo3D] Mock 패턴 파일 생성 실패: {e}")
        
        return {
            "status": "success",
            "pattern_path": pattern_path,
            "pattern_info": {
                "type": pattern_data["garment_type"],
                "components": pattern_data["components"],
            },
            "message": "패턴 생성이 완료되었습니다. (Mock 모드)"
        }
    
    def _mock_convert_to_3d(self, pattern_result: Dict[str, Any]) -> Dict[str, Any]:
        """Mock 3D 변환"""
        output_dir = project_root / "outputs" / "3d_models"
        output_dir.mkdir(parents=True, exist_ok=True)
        mesh_path = str(output_dir / "garment.obj")
        
        # 실제 Mock OBJ 파일 생성 (간단한 3D 메시)
        try:
            with open(mesh_path, 'w', encoding='utf-8') as f:
                # 간단한 Mock OBJ 파일 (큐브 형태)
                f.write("# Mock 3D Garment Mesh\n")
                f.write("# Generated by Mock Converter\n")
                f.write("g garment_mock\n")
                
                # 정점 (vertices) - 간단한 박스 형태
                vertices = [
                    (-1, -1, -1),  # 0
                    (1, -1, -1),   # 1
                    (1, 1, -1),    # 2
                    (-1, 1, -1),   # 3
                    (-1, -1, 1),   # 4
                    (1, -1, 1),    # 5
                    (1, 1, 1),     # 6
                    (-1, 1, 1),    # 7
                ]
                
                for v in vertices:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                
                # 면 (faces) - 박스의 6개 면
                faces = [
                    (0, 1, 2, 3),  # 앞면
                    (4, 7, 6, 5),  # 뒷면
                    (0, 4, 5, 1),  # 아래면
                    (2, 6, 7, 3),  # 위면
                    (0, 3, 7, 4),  # 왼쪽면
                    (1, 5, 6, 2),  # 오른쪽면
                ]
                
                for face in faces:
                    f.write(f"f {' '.join([str(i+1) for i in face])}\n")
            
            print(f"[Extensions2DTo3D] Mock 3D 메시 파일 생성 완료: {mesh_path}")
        except Exception as e:
            print(f"[Extensions2DTo3D] Mock 3D 메시 파일 생성 실패: {e}")
        
        return {
            "status": "success",
            "mesh_path": mesh_path,
            "mesh_info": {
                "vertices": 8,
                "faces": 6,
                "format": "obj"
            },
            "message": "3D 변환이 완료되었습니다. (Mock 모드)"
        }
    
    def _mock_render(self, mesh_result: Dict[str, Any]) -> str:
        """Mock 렌더링"""
        output_dir = project_root / "outputs" / "renders"
        output_dir.mkdir(parents=True, exist_ok=True)
        render_path = str(output_dir / "garment_render.png")
        return render_path


# 도구 함수로 사용하기 위한 래퍼
def extensions_2d_to_3d_tool(action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """도구 함수 래퍼"""
    tool = Extensions2DTo3D()
    return tool.execute(action, parameters, context)

```


린터 오류 확인 및 수정 중.



구현 완료. 요구사항에 맞게 Integration Switch를 추가하고 3D 변환 기능을 구현했습니다.

## 구현 완료 사항

### 1. 마이크로서비스 엔드포인트 추가 (`agentic_system/chatgarment_service/main.py`)
- `/api/v1/convert_to_3d` 엔드포인트 추가
- 2D 패턴 JSON 파일 경로를 입력받아 GarmentCodeRC 시뮬레이션 수행
- 최종 3D 의상 파일(.obj) 생성 및 반환

### 2. Integration Switch 추가 (`Extensions2DTo3D` 클래스)
- 두 가지 통합 방식 지원:
  - 로컬 통합 (Local Integration): 내부 함수로 직접 실행
  - 마이크로 서비스 호출 (Microservice): 외부 API(Port: 9000)로 원격 호출
- 환경 변수로 제어 가능: `EXTENSIONS_INTEGRATION_MODE` (기본값: "local")

### 3. `_convert_to_3d` 메서드 개선
- Integration Switch에 따라 자동 선택:
  - 로컬 모드: `run_garmentcode_sim.py` 스크립트 직접 실행
  - 마이크로 서비스 모드: 포트 9000 API 호출
- 실패 시 자동 폴백 (마이크로 서비스 → 로컬 → Mock)

### 4. 마이크로서비스 클라이언트 확장 (`extensions_service.py`)
- `convert_to_3d()` 메서드 추가
- `chatgarment_service_tool()`에 "convert_to_3d" 액션 지원

## 사용 방법

### 로컬 통합 모드 (기본값)
```python
tool = Extensions2DTo3D(integration_mode="local")
# 또는 환경 변수 설정 안 함 (기본값)
```

### 마이크로 서비스 모드
```python
tool = Extensions2DTo3D(integration_mode="microservice")
# 또는 환경 변수 설정
# export EXTENSIONS_INTEGRATION_MODE=microservice
# export CHATGARMENT_SERVICE_URL=http://localhost:9000
```

### 처리 과정
1. 입력: 2D 패턴 데이터(JSON) 파일 경로
2. 처리: GarmentCodeRC 모듈이 시뮬레이션 수행
3. 출력: 최종 3D 의상 파일(.obj) 생성 및 반환

모든 구현이 완료되었고 린터 오류도 없습니다.

```python
tool = Extensions2DTo3D(integration_mode="local")
# 또는 환경 변수 설정 안 함 (기본값)
```

```python
tool = Extensions2DTo3D(integration_mode="microservice")
# 또는 환경 변수 설정
# export EXTENSIONS_INTEGRATION_MODE=microservice
# export CHATGARMENT_SERVICE_URL=http://localhost:9000
```

---

**User**

첨부한 이미지를 모두 분석 및 파악 후, 각각 파일이 어디에 존재하는지 구체적으로 안내해주세요! 우선, Agent Runtime(Agent1)-종합감독 : File: core_agnet_runtime.py > F.LLM(Agent 2) - 작업 지시 전문가: File: core_llm.py 파일은 어디에 있나요? 만일 없다면, 유사한 또는 파일이름은 달라도 같은 기능을 하는 파일을 모두 찾아서 알려주세요! 입력한 내용 외에도 연관된 파일들을 모두 찾아서 자세히 안내해 주세요! 예를들어, tools_registry['extensions_2d_to_3d']()은 어떤 기능을 하는 기능인지 파일인지등등 자세히 안내해주세요! 정리해보자면, 첫 째: Agent Runtime(Agent1)-종합감독 : File: core_agnet_runtime.py > 둘 째: F.LLM(Agent 2) - 작업 지시 전문가: File: core_llm.py 어디에 존재하는지? 또는 없다면 유사한 기능을 하는 파일은 무엇인지 자세히 알려주세요!

---

**Cursor**


이미지의 워크플로우 다이어그램을 분석하고, 언급된 파일들의 위치를 확인 중입니다.



파일 위치와 연관 파일 확인 중입니다.



파일 위치와 연관 파일 정리 중입니다.



파일 위치와 연관 파일 정리:

## 파일 위치 및 상세 분석

### 1. Agent Runtime (Agent1) - 종합감독

#### 실제 파일 위치
- 파일명: `agent_runtime.py` (다이어그램의 `core_agent_runtime.py`와 동일)
- 전체 경로: `agentic_system/core/agent_runtime.py`
- 클래스명: `AgentRuntime`

#### 주요 기능 및 구조

```30:51:agentic_system/core/agent_runtime.py
class AgentRuntime:
    """
    Agent Runtime - Agent 1 (종합 감독 에이전트)
    
    전체 프로세스를 오케스트레이션하는 핵심 엔진
    """
    
    def __init__(
        self,
        agent2: Optional[FLLM] = None,
        memory_manager: Optional[MemoryManager] = None,
        max_retries: int = 1
    ):
        self.agent2 = agent2 or FLLM()
        self.memory_manager = memory_manager or MemoryManager()
        self.max_retries = max_retries
        self.name = "Agent Runtime (Agent 1)"
        self.tools_registry: Dict[str, Callable] = {}
    
    def register_tool(self, tool_name: str, tool_function: Callable):
        """도구 등록"""
        self.tools_registry[tool_name] = tool_function
```

#### 3단계 프로세스

1. 인식 (Perception) - `_analyze_user_intent()`
   - 사용자 의도 분석
   - 작업 유형 판단 (3D 생성 vs 상품 추천)

2. 판단 (Judgment) - `_create_abstract_plan()`
   - 추상적 계획 수립
   - Agent 2에게 전달

3. 행동 (Action) - `_execute_plan()`
   - 실행 계획 실행
   - 도구 호출 (`tools_registry` 사용)

#### 연관 파일
- `agentic_system/core/__init__.py`: 모듈 임포트 정의
- `agentic_system/core/memory.py`: 메모리 관리 (`MemoryManager`)
- `agentic_system/core/custom_ui.py`: UI 컴포넌트 인터페이스

---

### 2. F.LLM (Agent 2) - 작업 지시 전문가

#### 실제 파일 위치
- 파일명: `f_llm.py` (다이어그램의 `core_llm.py`와 동일)
- 전체 경로: `agentic_system/core/f_llm.py`
- 클래스명: `FLLM`

#### 주요 기능 및 구조

```39:77:agentic_system/core/f_llm.py
class FLLM:
    """
    Foundation LLM (F.LLM) - Agent 2
    
    작업 지시 전문가 에이전트로, Agent 1의 추상적 계획을
    구체적인 도구 호출 순서와 파라미터를 담은 JSON 형식의 실행 계획으로 변환
    
    InternVL2-8B 모델을 사용하여 멀티모달 입력 처리
    """
    
    def __init__(
        self, 
        model_name: str = "internvl2-8b",
        model_path: Optional[str] = None,
        rag_enabled: bool = False,
        use_llm: bool = True,
        device: str = "cuda"
    ):
        self.model_name = model_name
        self.rag_enabled = rag_enabled
        self.use_llm = use_llm
        self.name = "F.LLM (Agent 2)"
        
        # InternVL2 모델 초기화
        self.llm_model = None
        if use_llm and InternVL2Wrapper is not None:
            try:
                actual_device = device if device else ("cuda" if self._check_cuda() else "cpu")
                self.llm_model = InternVL2Wrapper(
                    model_path=model_path,
                    device=actual_device
                )
                print(f"InternVL2-8B 모델이 준비되었습니다. (디바이스: {actual_device})")
            except Exception as e:
                print(f"InternVL2 모델 로딩 경고: {str(e)}")
                print("규칙 기반 모드로 동작합니다.")
                self.llm_model = None
                self.use_llm = False
```

#### 핵심 메서드
- `generate_execution_plan()`: 추상적 계획을 구체적 실행 계획(JSON)으로 변환

#### 연관 파일
- `agentic_system/models/internvl2_wrapper.py`: InternVL2-8B 모델 래퍼
- `agentic_system/core/__init__.py`: `FLLM`, `Agent2` 임포트

---

### 3. `tools_registry['extensions_2d_to_3d']()` 상세 분석

#### 도구 등록 위치
- 파일: `agentic_system/api/main.py`
- 등록 코드:

```93:95:agentic_system/api/main.py
# 도구 등록
agent_runtime.register_tool("extensions_2d_to_3d", extensions_2d_to_3d_tool)
agent_runtime.register_tool("function_product_search", product_search_function_tool)
```

#### 도구 함수 정의
- 파일: `agentic_system/tools/extensions.py`
- 함수명: `extensions_2d_to_3d_tool()`

```963:967:agentic_system/tools/extensions.py
# 도구 함수로 사용하기 위한 래퍼
def extensions_2d_to_3d_tool(action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """도구 함수 래퍼"""
    tool = Extensions2DTo3D()
    return tool.execute(action, parameters, context)
```

#### 도구 실행 흐름

```213:226:agentic_system/core/agent_runtime.py
            # 도구 실행
            if tool_name in self.tools_registry:
                try:
                    print(f"[AgentRuntime._execute_plan] 도구 실행 중: {tool_name}.{action}")
                    tool_func = self.tools_registry[tool_name]
                    step_result = tool_func(action, parameters, execution_context)
                    print(f"[AgentRuntime._execute_plan] 도구 실행 완료: {tool_name}.{action}")
                    results[step_id] = {
                        "status": "success",
                        "result": step_result,
                        "step_id": step_id
                    }
                    # 컨텍스트에 실제 결과 저장 (다음 단계에서 사용)
                    execution_context[f"step_{step_id}"] = step_result
                    execution_context[f"step_{step_id}_result"] = step_result
```

#### 실행 예시
```python
# Agent Runtime에서 도구 호출
tool_func = self.tools_registry['extensions_2d_to_3d']
result = tool_func(
    action="analyze_image",
    parameters={"image_path": "/path/to/image.jpg"},
    context={}
)
```

---

## 전체 파일 구조 요약

### Core 컴포넌트 (`agentic_system/core/`)
```
agentic_system/core/
├── __init__.py              # 모듈 임포트 정의
├── agent_runtime.py         # ✅ Agent Runtime (Agent1) - 종합감독
├── f_llm.py                 # ✅ F.LLM (Agent 2) - 작업 지시 전문가
├── memory.py                # 메모리 관리 (MemoryManager)
└── custom_ui.py             # UI 컴포넌트 인터페이스
```

### Tools (`agentic_system/tools/`)
```
agentic_system/tools/
├── __init__.py
├── extensions.py            # ✅ Extensions2DTo3D 클래스 및 extensions_2d_to_3d_tool() 함수
├── extensions_service.py    # 마이크로서비스 클라이언트
├── chatgarment_integration.py  # ChatGarment Pipeline 래퍼
└── functions.py             # 상품 검색 도구
```

### API 서버 (`agentic_system/api/`)
```
agentic_system/api/
└── main.py                  # ✅ 도구 등록 및 API 엔드포인트 정의
```

---

## 파일명 매핑 정리

| 다이어그램 파일명 | 실제 파일명 | 전체 경로 |
|-----------------|------------|----------|
| `core_agent_runtime.py` | `agent_runtime.py` | `agentic_system/core/agent_runtime.py` |
| `core_llm.py` | `f_llm.py` | `agentic_system/core/f_llm.py` |
| `tools/extensions.py` | `extensions.py` | `agentic_system/tools/extensions.py` |

---

## 연관 파일 및 기능

### 1. 도구 등록 관련
- `agentic_system/api/main.py` (라인 94): `agent_runtime.register_tool("extensions_2d_to_3d", extensions_2d_to_3d_tool)`
- `agentic_system/core/agent_runtime.py` (라인 47-51): `tools_registry` 딕셔너리 및 `register_tool()` 메서드

### 2. 도구 실행 관련
- `agentic_system/core/agent_runtime.py` (라인 213-226): `_execute_plan()` 메서드에서 도구 호출
- `agentic_system/tools/extensions.py` (라인 964-967): `extensions_2d_to_3d_tool()` 래퍼 함수

### 3. Agent 간 통신
- `agentic_system/core/agent_runtime.py` (라인 78-84): Agent 1 → Agent 2 호출 (`self.agent2.generate_execution_plan()`)
- `agentic_system/core/f_llm.py` (라인 86-143): Agent 2의 `generate_execution_plan()` 메서드

### 4. Integration Switch 관련
- `agentic_system/tools/extensions.py` (라인 58-96): `Extensions2DTo3D` 클래스의 Integration Switch 구현
- `agentic_system/tools/extensions_service.py`: 마이크로서비스 클라이언트

---

## 요약

1. Agent Runtime (Agent1): `agentic_system/core/agent_runtime.py`에 `AgentRuntime` 클래스로 구현
2. F.LLM (Agent 2): `agentic_system/core/f_llm.py`에 `FLLM` 클래스로 구현
3. `tools_registry['extensions_2d_to_3d']()`: `agentic_system/api/main.py`에서 등록, `agentic_system/tools/extensions.py`의 `extensions_2d_to_3d_tool()` 함수가 실행됨

모든 파일이 존재하며, 다이어그램의 파일명과 실제 파일명이 약간 다르지만 기능은 동일합니다.

```python
class AgentRuntime:
    """
    Agent Runtime - Agent 1 (종합 감독 에이전트)
    
    전체 프로세스를 오케스트레이션하는 핵심 엔진
    """
    
    def __init__(
        self,
        agent2: Optional[FLLM] = None,
        memory_manager: Optional[MemoryManager] = None,
        max_retries: int = 1
    ):
        self.agent2 = agent2 or FLLM()
        self.memory_manager = memory_manager or MemoryManager()
        self.max_retries = max_retries
        self.name = "Agent Runtime (Agent 1)"
        self.tools_registry: Dict[str, Callable] = {}
    
    def register_tool(self, tool_name: str, tool_function: Callable):
        """도구 등록"""
        self.tools_registry[tool_name] = tool_function
```

```python
class FLLM:
    """
    Foundation LLM (F.LLM) - Agent 2
    
    작업 지시 전문가 에이전트로, Agent 1의 추상적 계획을
    구체적인 도구 호출 순서와 파라미터를 담은 JSON 형식의 실행 계획으로 변환
    
    InternVL2-8B 모델을 사용하여 멀티모달 입력 처리
    """
    
    def __init__(
        self, 
        model_name: str = "internvl2-8b",
        model_path: Optional[str] = None,
        rag_enabled: bool = False,
        use_llm: bool = True,
        device: str = "cuda"
    ):
        self.model_name = model_name
        self.rag_enabled = rag_enabled
        self.use_llm = use_llm
        self.name = "F.LLM (Agent 2)"
        
        # InternVL2 모델 초기화
        self.llm_model = None
        if use_llm and InternVL2Wrapper is not None:
            try:
                actual_device = device if device else ("cuda" if self._check_cuda() else "cpu")
                self.llm_model = InternVL2Wrapper(
                    model_path=model_path,
                    device=actual_device
                )
                print(f"InternVL2-8B 모델이 준비되었습니다. (디바이스: {actual_device})")
            except Exception as e:
                print(f"InternVL2 모델 로딩 경고: {str(e)}")
                print("규칙 기반 모드로 동작합니다.")
                self.llm_model = None
                self.use_llm = False
```

```python
# 도구 등록
agent_runtime.register_tool("extensions_2d_to_3d", extensions_2d_to_3d_tool)
agent_runtime.register_tool("function_product_search", product_search_function_tool)
```

```python
# 도구 함수로 사용하기 위한 래퍼
def extensions_2d_to_3d_tool(action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """도구 함수 래퍼"""
    tool = Extensions2DTo3D()
    return tool.execute(action, parameters, context)
```

```python
            # 도구 실행
            if tool_name in self.tools_registry:
                try:
                    print(f"[AgentRuntime._execute_plan] 도구 실행 중: {tool_name}.{action}")
                    tool_func = self.tools_registry[tool_name]
                    step_result = tool_func(action, parameters, execution_context)
                    print(f"[AgentRuntime._execute_plan] 도구 실행 완료: {tool_name}.{action}")
                    results[step_id] = {
                        "status": "success",
                        "result": step_result,
                        "step_id": step_id
                    }
                    # 컨텍스트에 실제 결과 저장 (다음 단계에서 사용)
                    execution_context[f"step_{step_id}"] = step_result
                    execution_context[f"step_{step_id}_result"] = step_result
```

```python
# Agent Runtime에서 도구 호출
tool_func = self.tools_registry['extensions_2d_to_3d']
result = tool_func(
    action="analyze_image",
    parameters={"image_path": "/path/to/image.jpg"},
    context={}
)
```

```plaintext
agentic_system/core/
├── __init__.py              # 모듈 임포트 정의
├── agent_runtime.py         # ✅ Agent Runtime (Agent1) - 종합감독
├── f_llm.py                 # ✅ F.LLM (Agent 2) - 작업 지시 전문가
├── memory.py                # 메모리 관리 (MemoryManager)
└── custom_ui.py             # UI 컴포넌트 인터페이스
```

```plaintext
agentic_system/tools/
├── __init__.py
├── extensions.py            # ✅ Extensions2DTo3D 클래스 및 extensions_2d_to_3d_tool() 함수
├── extensions_service.py    # 마이크로서비스 클라이언트
├── chatgarment_integration.py  # ChatGarment Pipeline 래퍼
└── functions.py             # 상품 검색 도구
```

```plaintext
agentic_system/api/
└── main.py                  # ✅ 도구 등록 및 API 엔드포인트 정의
```

