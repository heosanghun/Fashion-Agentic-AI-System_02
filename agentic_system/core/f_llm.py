"""
F.LLM (Foundation LLM) Component - Agent 2
작업 지시 전문가 에이전트 (Agent 2)

역할:
- Agent 1의 계획을 받아 구체적인 실행 계획 생성
- JSON 형식의 실행 계획 출력
- RAG를 통한 지식 보강
- InternVL2-8B 모델 통합
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import json
from datetime import datetime
import sys
from pathlib import Path
import threading

# InternVL2 래퍼 임포트
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
try:
    from agentic_system.models import InternVL2Wrapper
except ImportError:
    InternVL2Wrapper = None


class ExecutionPlan(BaseModel):
    """실행 계획 모델"""
    plan_id: str
    steps: List[Dict[str, Any]]
    tools_required: List[str]
    parameters: Dict[str, Any]
    estimated_time: Optional[float] = None
    created_at: str


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
        
    def _check_cuda(self) -> bool:
        """CUDA 사용 가능 여부 확인"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
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
        
        Args:
            abstract_plan: Agent 1이 생성한 추상적 계획
            context: 추가 컨텍스트 정보
            rag_context: RAG를 통해 검색된 지식
            user_text: 사용자 입력 텍스트
            image_path: 사용자 입력 이미지 경로
            
        Returns:
            ExecutionPlan: 구체적인 실행 계획
        """
        print(f"[F.LLM] 실행 계획 생성 시작: plan_type={abstract_plan.get('plan_type')}, use_llm={self.use_llm}, has_llm_model={self.llm_model is not None}, has_user_text={user_text is not None}")
        
        # LLM을 사용한 계획 생성 (PoC 단계에서는 비활성화 - 성능 문제로 인해)
        # 향후 Pilot 단계에서 활성화 예정
        use_llm_for_now = False  # LLM 추론이 너무 느려서 임시 비활성화
        
        if use_llm_for_now and self.use_llm and self.llm_model is not None and user_text:
            print("[F.LLM] LLM 기반 계획 생성 시도...")
            enhanced_plan = self._generate_plan_with_llm(
                abstract_plan, user_text, image_path, context, rag_context
            )
            print("[F.LLM] LLM 기반 계획 생성 완료")
        else:
            print("[F.LLM] 규칙 기반 계획 생성 (PoC 단계)")
            # 규칙 기반 계획 생성 (Fallback)
            enhanced_plan = self._enhance_with_rag(abstract_plan, rag_context) if self.rag_enabled and rag_context else abstract_plan
        
        # 실행 단계 생성
        print("[F.LLM] 실행 단계 생성 시작...")
        steps = self._create_execution_steps(enhanced_plan, context)
        print(f"[F.LLM] 실행 단계 생성 완료: {len(steps)}개 단계")
        
        # 필요한 도구 목록 추출
        tools_required = self._extract_required_tools(steps)
        
        # 실행 계획 생성
        execution_plan = ExecutionPlan(
            plan_id=f"plan_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            steps=steps,
            tools_required=tools_required,
            parameters=self._extract_parameters(enhanced_plan),
            estimated_time=self._estimate_execution_time(steps),
            created_at=datetime.now().isoformat()
        )
        
        print(f"[F.LLM] 실행 계획 생성 완료: plan_id={execution_plan.plan_id}")
        return execution_plan
    
    def _generate_plan_with_llm(
        self,
        abstract_plan: Dict[str, Any],
        user_text: str,
        image_path: Optional[str],
        context: Optional[Dict[str, Any]],
        rag_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        LLM을 사용하여 계획 생성
        
        InternVL2-8B 모델을 사용하여 사용자 입력과 이미지를 분석하고
        구체적인 실행 계획을 생성
        """
        if self.llm_model is None:
            return abstract_plan
        
        # LLM 모델이 로드되지 않았으면 로드
        if self.llm_model.model is None:
            # 모델 경로 존재 여부 확인
            from pathlib import Path
            model_path = Path(self.llm_model.model_path)
            if not model_path.exists():
                print(f"[F.LLM] WARNING: InternVL2 모델 경로가 존재하지 않습니다: {model_path}")
                print("[F.LLM] 규칙 기반 모드로 전환합니다.")
                return abstract_plan
            
            try:
                print(f"[F.LLM] InternVL2 모델 로딩 시도 중: {model_path}")
                self.llm_model.load_model()
            except Exception as e:
                print(f"[F.LLM] ERROR: LLM 모델 로딩 실패: {str(e)}")
                print("[F.LLM] 규칙 기반 모드로 전환합니다.")
                return abstract_plan
        
        # 프롬프트 구성
        prompt = self._build_planning_prompt(abstract_plan, user_text, context, rag_context)
        
        try:
            # LLM 추론 (타임아웃 설정)
            # threading은 이미 임포트됨
            
            response = None
            error_occurred = threading.Event()
            
            def llm_inference():
                nonlocal response
                try:
                    response = self.llm_model.generate_text(
                        prompt=prompt,
                        image_path=image_path,
                        max_new_tokens=512
                    )
                except Exception as e:
                    print(f"[F.LLM] ERROR: LLM 추론 오류: {str(e)}")
                    error_occurred.set()
            
            # 별도 스레드에서 추론 실행
            print("[F.LLM] LLM 추론 시작 (별도 스레드, 타임아웃: 5초)...")
            inference_thread = threading.Thread(target=llm_inference)
            inference_thread.daemon = True
            inference_thread.start()
            inference_thread.join(timeout=5)  # 5초 타임아웃 (더 짧게 설정)
            
            if inference_thread.is_alive():
                print("[F.LLM] WARNING: LLM 추론 타임아웃 (5초 초과). 규칙 기반 모드로 전환합니다.")
                return abstract_plan
            
            if error_occurred.is_set():
                print("[F.LLM] WARNING: LLM 추론 오류 발생. 규칙 기반 모드로 전환합니다.")
                return abstract_plan
            
            if response is None:
                print("[F.LLM] WARNING: LLM 응답이 없습니다. 규칙 기반 모드로 전환합니다.")
                return abstract_plan
            
            # 응답 파싱 및 계획 강화
            enhanced_plan = self._parse_llm_response(response, abstract_plan)
            return enhanced_plan
            
        except Exception as e:
            print(f"[F.LLM] ERROR: LLM 계획 생성 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return abstract_plan
    
    def _build_planning_prompt(
        self,
        abstract_plan: Dict[str, Any],
        user_text: str,
        context: Optional[Dict[str, Any]],
        rag_context: Optional[Dict[str, Any]]
    ) -> str:
        """계획 생성을 위한 프롬프트 구성"""
        prompt = f"""당신은 패션 AI 가상 피팅 시스템의 작업 지시 전문가 에이전트입니다.

사용자 요청: {user_text}

추상적 계획:
- 목표: {abstract_plan.get('goal', '')}
- 유형: {abstract_plan.get('plan_type', '')}
- 단계: {', '.join(abstract_plan.get('steps', []))}

다음 형식으로 구체적인 실행 계획을 생성해주세요:

1. 각 단계별로 필요한 도구(Tool)를 지정
2. 각 단계의 파라미터를 명확히 정의
3. 단계 간 의존성을 명시

JSON 형식으로 반환하거나, 자연어로 단계별 실행 계획을 설명해주세요."""
        
        if rag_context:
            prompt += f"\n\n참고 정보: {rag_context.get('rag_suggestions', [])}"
        
        return prompt
    
    def _parse_llm_response(self, response: str, original_plan: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 응답 파싱 및 계획 강화"""
        enhanced_plan = original_plan.copy()
        
        # LLM 응답에서 유용한 정보 추출
        enhanced_plan["llm_enhanced"] = True
        enhanced_plan["llm_suggestions"] = response
        
        # 간단한 키워드 기반 파라미터 추출
        if "색상" in response or "color" in response.lower():
            enhanced_plan["parameters"]["needs_color_analysis"] = True
        if "스타일" in response or "style" in response.lower():
            enhanced_plan["parameters"]["needs_style_analysis"] = True
        
        return enhanced_plan
    
    def _enhance_with_rag(
        self, 
        plan: Dict[str, Any], 
        rag_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        RAG 컨텍스트를 사용하여 계획 강화
        
        PoC 단계에서는 Mock RAG 사용
        """
        enhanced = plan.copy()
        if "rag_suggestions" in rag_context:
            enhanced["rag_enhanced"] = True
            enhanced["suggestions"] = rag_context["rag_suggestions"]
        return enhanced
    
    def _create_execution_steps(
        self, 
        plan: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        실행 단계 생성
        
        예시:
        [
            {
                "step_id": 1,
                "tool": "gemini_tryon",
                "action": "try_on",
                "parameters": {...},
                "dependencies": []
            },
            ...
        ]
        """
        steps = []
        
        # 계획 유형에 따라 단계 생성
        plan_type = plan.get("type") or plan.get("plan_type", "unknown")
        print(f"[F.LLM._create_execution_steps] plan_type 확인: {plan_type}")
        print(f"[F.LLM._create_execution_steps] plan keys: {list(plan.keys())}")
        
        if plan_type == "3d_generation":
            print("[F.LLM._create_execution_steps] 3D 생성 단계 생성")
            steps = self._create_3d_generation_steps(plan, context)
        elif plan_type == "garment_recommendation":
            print("[F.LLM._create_execution_steps] 상품 추천 단계 생성")
            steps = self._create_recommendation_steps(plan, context)
        else:
            print(f"[F.LLM._create_execution_steps] 기본 단계 생성 (plan_type={plan_type})")
            # 기본 단계 생성
            steps = [
                {
                    "step_id": 1,
                    "tool": "gemini_tryon",
                    "action": "process_request",
                    "parameters": plan.get("parameters", {}),
                    "dependencies": []
                }
            ]
        
        print(f"[F.LLM._create_execution_steps] 생성된 단계 수: {len(steps)}")
        return steps
    
    def _create_3d_generation_steps(
        self, 
        plan: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """3D/가상 피팅 경로의 실행 단계 생성 (Gemini Try-On 단일 단계)"""
        steps = [
            {
                "step_id": 1,
                "tool": "gemini_tryon",
                "action": "try_on",
                "parameters": {
                    "image_path": context.get("image_path") if context else None,
                    "text_description": context.get("text") if context else None,
                    "person_image_path": context.get("person_image_path") if context else None,
                },
                "dependencies": []
            }
        ]
        return steps
    
    def _create_recommendation_steps(
        self, 
        plan: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """상품 추천 경로의 실행 단계 생성"""
        steps = [
            {
                "step_id": 1,
                "tool": "function_product_search",
                "action": "search_products",
                "parameters": {
                    "query": context.get("text") if context else "",
                    "filters": plan.get("filters", {})
                },
                "dependencies": []
            },
            {
                "step_id": 2,
                "tool": "function_product_search",
                "action": "match_recommendations",
                "parameters": {},
                "dependencies": [1]
            }
        ]
        return steps
    
    def _extract_required_tools(self, steps: List[Dict[str, Any]]) -> List[str]:
        """실행 단계에서 필요한 도구 목록 추출"""
        tools = set()
        for step in steps:
            if "tool" in step:
                tools.add(step["tool"])
        return list(tools)
    
    def _extract_parameters(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """계획에서 파라미터 추출"""
        return plan.get("parameters", {})
    
    def _estimate_execution_time(self, steps: List[Dict[str, Any]]) -> float:
        """실행 예상 시간 추정 (초 단위)"""
        # 간단한 추정: 각 단계당 평균 5초
        base_time = len(steps) * 5
        return base_time


# Agent 2는 FLLM의 별칭
Agent2 = FLLM
