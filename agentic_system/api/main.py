"""
FastAPI Main Server
Fashion Agentic AI System API 서버
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import uvicorn
import sys
from pathlib import Path
import os
import subprocess

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agentic_system"))

# .env 파일 로드 (프로젝트 루트, UTF-8 BOM 제거하여 키 이름 깨짐 방지)
_env_path = project_root / ".env"
try:
    from dotenv import load_dotenv
    if _env_path.exists():
        try:
            load_dotenv(_env_path, encoding="utf-8-sig")
        except TypeError:
            load_dotenv(_env_path)
        print(f"[API] .env 로드됨: {_env_path}")
except ImportError:
    pass

# 환경 변수: Gemini API (가상 피팅용)
if "GEMINI_API_KEY" not in os.environ:
    try:
        result = subprocess.run(
            ["powershell", "-Command", "[System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            os.environ["GEMINI_API_KEY"] = result.stdout.strip()
    except Exception:
        pass
print(f"[API] GEMINI_API_KEY 설정 여부: {'예' if os.environ.get('GEMINI_API_KEY') else '아니오 (Mock 동작)'}")

# OpenAI API 키 (대화 의도 시 LLM 응답용) — 여러 이름·BOM·줄바꿈 제거
def _normalize_key(s: str) -> str:
    if not s:
        return ""
    return s.replace("\r", "").replace("\n", "").strip()

def _get_openai_key():
    key = _normalize_key(os.environ.get("OpenAI_API_Key") or os.environ.get("OPENAI_API_KEY") or "")
    if key:
        return key
    for k, v in os.environ.items():
        if v and "openai" in k.lower() and "key" in k.lower():
            key = _normalize_key(v)
            if key:
                return key
    return ""

_openai_key = _get_openai_key()
if _openai_key:
    os.environ["OPENAI_API_KEY"] = _openai_key  # AgentRuntime 에서 통일해서 읽도록
    print(f"[API] OpenAI API 키 로드됨 (대화 LLM 사용 가능, 앞 8자: {_openai_key[:8]}...)")
else:
    print("[API] OpenAI API 키 없음 — 대화 시 고정 안내 문구만 사용됩니다. .env 에 OpenAI_API_Key= 또는 OPENAI_API_KEY= 설정 후 서버 재시작하세요.")

from agentic_system.core import CustomUI, AgentRuntime, FLLM
from agentic_system.core.memory import MemoryManager
from agentic_system.tools.gemini_tryon import gemini_tryon_tool
from agentic_system.tools.functions import product_search_function_tool
from agentic_system.data_stores.rag import RAGStore

app = FastAPI(
    title="Fashion Agentic AI System API",
    description="패션 Agentic AI 가상 피팅 POC 개발 - API 서버",
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

# 전역 컴포넌트 초기화
memory_manager = MemoryManager()
rag_store = RAGStore()

# InternVL2-8B 모델 통합 (자동 디바이스 감지)
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
agent2 = FLLM(
    model_name="internvl2-8b",
    model_path=None,  # 자동 경로 감지
    rag_enabled=True,  # 외부(웹) + 내부(로컬) RAG 사용
    use_llm=True,  # InternVL2 모델 사용
    device=device
)
agent_runtime = AgentRuntime(agent2=agent2, memory_manager=memory_manager, rag_store=rag_store)

# 도구 등록 (가상 피팅: Gemini Try-On, 상품 검색: Function)
agent_runtime.register_tool("gemini_tryon", gemini_tryon_tool)
agent_runtime.register_tool("function_product_search", product_search_function_tool)

custom_ui = CustomUI()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Fashion Agentic AI System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


@app.post("/api/v1/tryon")
async def tryon_direct(
    image: UploadFile = File(..., description="입을 옷 사진 (의류)"),
    person_image: UploadFile = File(..., description="내 사진 (인물)"),
    session_id: Optional[str] = Form(None),
):
    """
    직통 가상 피팅 API — Agent/실행 계획 경유 없이 Gemini Try-On만 호출합니다.
    POC 뼈대(Agent 1 → Agent 2 → 실행 계획)로 인한 context 누락 여부를 검증할 때 사용하세요.
    """
    try:
        sid = session_id or "direct"
        upload_dir = project_root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        path_garment = (upload_dir / f"{sid}_garment_{image.filename}").resolve()
        path_person = (upload_dir / f"{sid}_person_{person_image.filename}").resolve()
        with open(path_garment, "wb") as f:
            f.write(await image.read())
        with open(path_person, "wb") as f:
            f.write(await person_image.read())
        image_path = str(path_garment)
        person_image_path = str(path_person)
        if not path_garment.exists() or not path_person.exists():
            print(f"[API /tryon] 경고: 파일 미존재 garment={path_garment.exists()}, person={path_person.exists()}")
        print(f"[API /tryon] 직통 Try-On: image_path={image_path}, person_image_path={person_image_path}")

        params = {
            "image_path": image_path,
            "person_image_path": person_image_path,
            "text_description": "입혀줘",
        }
        context = {
            "image_path": image_path,
            "person_image_path": person_image_path,
            "text": "입혀줘",
        }
        tool_result = gemini_tryon_tool("try_on", params, context)

        result = {
            "status": tool_result.get("status", "success"),
            "message": tool_result.get("message", ""),
            "data": {
                "steps": {"1": {"result": tool_result}},
                "final_result": {"result": tool_result},
                "plan_id": "direct_tryon",
            },
            "visualization": {},
            "chat_only": False,
        }
        response = custom_ui.format_output(result)
        return JSONResponse(content=response)
    except Exception as e:
        import traceback
        print(f"[API /tryon] 오류: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/request")
async def process_request(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    person_image: Optional[UploadFile] = File(None),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    사용자 요청 처리
    
    - image: 입을 옷 사진 (의류 이미지)
    - person_image: 내 사진 (인물 이미지)
    가상 피팅(Try-On) 시 두 이미지 모두 있으면 더 정확한 결과를 위해 사용됩니다.
    """
    try:
        sid = session_id or "temp"
        print(f"[API] 요청 수신: text={text is not None}, image={image is not None}, person_image={person_image is not None}, session_id={sid}")
        
        upload_dir = project_root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        image_path = None
        person_image_path = None
        if image:
            path = upload_dir / f"{sid}_garment_{image.filename}"
            with open(path, "wb") as f:
                f.write(await image.read())
            image_path = str(path)
            print(f"[API] 의류 이미지 저장: {image_path}")
        if person_image:
            path = upload_dir / f"{sid}_person_{person_image.filename}"
            with open(path, "wb") as f:
                f.write(await person_image.read())
            person_image_path = str(path)
            print(f"[API] 인물 이미지 저장: {person_image_path}")
        if person_image_path:
            print("[API] person_image_path 있음 → Try-On 시 Gemini 인물+의류 합성 가능")
        # Custom UI를 통한 입력 처리
        print("[API] Custom UI 입력 처리 시작...")
        payload = custom_ui.process_user_input(
            text=text,
            image_path=image_path,
            person_image_path=person_image_path,
            user_id=user_id,
            session_id=session_id
        )
        print(f"[API] Custom UI 입력 처리 완료: session_id={payload.session_id}")
        
        # Agent Runtime을 통한 요청 처리
        print("[API] Agent Runtime 요청 처리 시작...")
        result = agent_runtime.process_request(
            payload.dict(),
            session_id=session_id or payload.session_id
        )
        print(f"[API] Agent Runtime 요청 처리 완료: status={result.get('status')}")
        
        # 결과 포맷팅
        print("[API] 결과 포맷팅 시작...")
        response = custom_ui.format_output(result)
        print("[API] 결과 포맷팅 완료")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API] 오류 발생: {str(e)}")
        print(f"[API] 스택 트레이스:\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/request/json")
async def process_request_json(request_data: dict):
    """
    JSON 형식의 요청 처리
    
    Request Body:
    {
        "text": "이 옷을 입혀줘",
        "image_path": "/path/to/image.jpg",
        "user_id": "user123",
        "session_id": "session456"
    }
    """
    try:
        # Custom UI를 통한 입력 처리
        payload = custom_ui.process_user_input(
            text=request_data.get("text"),
            image_path=request_data.get("image_path"),
            user_id=request_data.get("user_id"),
            session_id=request_data.get("session_id")
        )
        
        # Agent Runtime을 통한 요청 처리
        result = agent_runtime.process_request(
            payload.dict(),
            session_id=request_data.get("session_id") or payload.session_id
        )
        
        # 결과 포맷팅
        response = custom_ui.format_output(result)
        
        return JSONResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/session/{session_id}/history")
async def get_session_history(session_id: str):
    """세션 대화 기록 조회"""
    try:
        memory = memory_manager.get_short_term_memory(session_id)
        history = memory.get_conversation_history()
        return {
            "session_id": session_id,
            "history": history,
            "context": memory.get_context()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/session/{session_id}")
async def clear_session(session_id: str):
    """세션 메모리 삭제"""
    try:
        memory_manager.clear_session(session_id)
        return {"message": f"Session {session_id} cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/file")
async def get_file(path: str = Query(..., description="파일 경로")):
    """
    파일 제공 엔드포인트
    
    보안을 위해 프로젝트 루트 내의 파일만 제공합니다.
    """
    try:
        file_path = Path(path)
        
        # 보안 체크: 프로젝트 루트 외부의 파일 접근 차단
        if not str(file_path.resolve()).startswith(str(project_root.resolve())):
            raise HTTPException(status_code=403, detail="접근할 수 없는 경로입니다.")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="파일이 아닙니다.")
        
        return FileResponse(
            path=str(file_path),
            media_type="image/png" if file_path.suffix.lower() in [".png", ".jpg", ".jpeg"] else "application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "agentic_system.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

