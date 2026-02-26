"""
Custom UI Component
사용자 입력을 받아 JSON Payload로 구조화하는 컴포넌트
"""

from typing import Dict, Optional, Union
from pydantic import BaseModel
import json
from datetime import datetime


class UserInput(BaseModel):
    """사용자 입력 데이터 모델"""
    text: Optional[str] = None
    image_path: Optional[str] = None
    image_data: Optional[bytes] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class JSONPayload(BaseModel):
    """Agent Runtime으로 전달되는 JSON Payload"""
    timestamp: str
    user_id: Optional[str]
    session_id: Optional[str]
    input_data: Dict
    metadata: Dict = {}


class CustomUI:
    """
    Custom UI 컴포넌트
    
    역할:
    - 사용자의 텍스트와 이미지 입력을 받음
    - 입력 데이터를 JSON Payload로 구조화
    - Agent Runtime으로 전달
    """
    
    def __init__(self):
        self.name = "CustomUI"
        
    def process_user_input(
        self, 
        text: Optional[str] = None,
        image_path: Optional[str] = None,
        image_data: Optional[bytes] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> JSONPayload:
        """
        사용자 입력을 처리하여 JSON Payload 생성
        
        Args:
            text: 사용자 텍스트 입력
            image_path: 이미지 파일 경로
            image_data: 이미지 바이너리 데이터
            user_id: 사용자 ID
            session_id: 세션 ID
            
        Returns:
            JSONPayload: 구조화된 JSON 페이로드
        """
        # 입력 검증
        if not text and not image_path and not image_data:
            raise ValueError("텍스트 또는 이미지 중 하나는 필수입니다.")
        
        # 입력 데이터 구조화
        input_data = {
            "text": text,
            "image_path": image_path,
            "has_image": bool(image_path or image_data)
        }
        
        # 이미지 데이터가 있으면 포함
        if image_data:
            input_data["image_data_size"] = len(image_data)
            # 실제 구현에서는 이미지를 인코딩하거나 저장 후 경로를 포함
        
        # 메타데이터 추가
        metadata = {
            "input_type": "text_and_image" if (text and (image_path or image_data)) else ("text" if text else "image"),
            "processed_at": datetime.now().isoformat()
        }
        
        # JSON Payload 생성
        payload = JSONPayload(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            session_id=session_id or self._generate_session_id(),
            input_data=input_data,
            metadata=metadata
        )
        
        return payload
    
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        return f"session_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    def format_output(self, result: Dict) -> Dict:
        """
        Agent Runtime에서 받은 결과를 사용자에게 보여줄 형식으로 변환
        
        Args:
            result: Agent Runtime의 결과
            
        Returns:
            Dict: 사용자용 결과 데이터
        """
        data = result.get("data", {})
        return {
            "status": result.get("status", "unknown"),
            "message": result.get("message", ""),
            "data": data,
            "visualization": result.get("visualization", {}),
            "thoughts": result.get("thoughts", {}),
            "steps": data.get("steps", result.get("steps", {})),
            "final_result": data.get("final_result", result.get("final_result", {})),
            "plan_id": data.get("plan_id", result.get("plan_id")),
            "chat_only": result.get("chat_only", False),
            "openai_used": result.get("openai_used"),
            "openai_error": result.get("openai_error"),
        }

