"""
Agent Runtime Component - Agent 1
종합 감독 에이전트 (Agent 1)

역할:
- 사용자 요청을 분석하여 큰 그림의 작업 계획 수립
- Agent 2에게 계획 전달 및 결과 수신
- 도구 실행 오케스트레이션
- 자기 수정 루프 관리
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import os

from .f_llm import FLLM, ExecutionPlan
from .memory import MemoryManager, ShortTermMemory
from pydantic import BaseModel


class AbstractPlan(BaseModel):
    """추상적 작업 계획"""
    plan_type: str  # "3d_generation" or "garment_recommendation"
    goal: str
    steps: List[str]  # 추상적 단계 설명
    parameters: Dict[str, Any]
    created_at: str


class AgentRuntime:
    """
    Agent Runtime - Agent 1 (종합 감독 에이전트)
    
    전체 프로세스를 오케스트레이션하는 핵심 엔진
    """
    
    def __init__(
        self,
        agent2: Optional[FLLM] = None,
        memory_manager: Optional[MemoryManager] = None,
        rag_store: Optional[Any] = None,
        max_retries: int = 1
    ):
        self.agent2 = agent2 or FLLM()
        self.memory_manager = memory_manager or MemoryManager()
        self.rag_store = rag_store
        self.max_retries = max_retries
        self.name = "Agent Runtime (Agent 1)"
        self.tools_registry: Dict[str, Callable] = {}
    
    def register_tool(self, tool_name: str, tool_function: Callable):
        """도구 등록"""
        self.tools_registry[tool_name] = tool_function
    
    def process_request(
        self,
        payload: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자 요청 처리
        
        전체 프로세스:
        1. 인식 (Perception): 요청 분석
        2. 판단 (Judgment): 계획 수립
        3. 행동 (Action): 도구 실행
        """
        # 세션 메모리 가져오기
        session_id = session_id or payload.get("session_id", "default")
        memory = self.memory_manager.get_short_term_memory(session_id)
        
        # 1. 인식 (Perception): 요청 분석
        user_intent = self._analyze_user_intent(payload)
        
        # 로컬 Try-On 전용 모드: 대화/RAG/추천 분기 없이 항상 가상 피팅만 실행
        try_on_only = os.environ.get("TRY_ON_ONLY", "").strip().lower() in ("1", "true", "yes")
        if try_on_only:
            input_data = payload.get("input_data", {}) or {}
            has_any = bool(input_data.get("text") or input_data.get("image_path") or input_data.get("person_image_path") or input_data.get("has_image"))
            user_intent = {
                "type": "3d_generation",
                "run_try_on": has_any,
                "confidence": 0.9,
                "text": (input_data.get("text") or "").lower(),
                "has_image": input_data.get("has_image", False),
            }
        
        # 대화/일상 멘트는 도구 실행 없이 바로 응답 (Try-On 전용 모드가 아닐 때만)
        if not try_on_only and user_intent.get("type") == "conversation":
            out = self._respond_conversation(payload, user_intent, memory, session_id)
            return {**out, "chat_only": True}
        
        # 정보성 질문 → RAG 검색 결과로만 응답 (Try-On 전용 모드가 아닐 때만)
        if not try_on_only and user_intent.get("type") == "information":
            out = self._respond_with_rag(payload, memory, session_id)
            return {**out, "chat_only": True}
        
        # 가상 피팅 의도지만 실행 요청 없고 이미지도 없으면 채팅만 (Try-On 전용 모드가 아닐 때만)
        if not try_on_only and user_intent.get("type") == "3d_generation" and not user_intent.get("run_try_on"):
            out = self._respond_try_on_prompt(payload, memory, session_id)
            return {**out, "chat_only": True}
        
        # Try-On 전용 모드에서 입력이 전혀 없으면 안내만 반환
        _input = payload.get("input_data") or {}
        if try_on_only and not _input.get("has_image") and not _input.get("text"):
            return {
                "status": "success",
                "message": "의류 사진과 내 사진(인물)을 올린 뒤 '입혀줘'를 보내주세요.",
                "data": {},
                "chat_only": True,
            }
        
        # 2. 판단 (Judgment): 추상적 계획 수립 (Agent 1 역할)
        abstract_plan = self._create_abstract_plan(user_intent, payload, memory)
        
        # RAG: 외부(인터넷) + 내부(로컬) 로 사용자 입력 관련 정보 검색
        user_text = (payload.get("input_data", {}) or {}).get("text", "")
        rag_context = None
        if self.rag_store and (user_text or abstract_plan.get("plan_type")):
            try:
                rag_context = self.rag_store.get_context(
                    abstract_plan.plan_type,
                    user_text or abstract_plan.get("parameters", {}).get("query", "")
                )
            except Exception as e:
                print(f"[AgentRuntime] RAG get_context 오류: {e}")
        
        # Agent 2에게 전달하여 구체적 실행 계획 생성
        input_data = payload.get("input_data", {})
        execution_plan = self.agent2.generate_execution_plan(
            abstract_plan.dict(),
            context=input_data,
            rag_context=rag_context,
            user_text=input_data.get("text"),
            image_path=input_data.get("image_path")
        )
        
        # 3. 행동 (Action): 실행 계획에 따라 도구 실행
        execution_result = self._execute_plan(execution_plan, memory)
        
        # 결과 검증 및 재시도 (자기 수정 루프)
        final_result = self._self_correction_loop(
            execution_plan,
            execution_result,
            memory
        )
        
        # 메모리에 대화 기록 저장
        memory.add_conversation(
            user_input=payload.get("input_data", {}).get("text", ""),
            agent_response=final_result.get("message", ""),
            metadata={"plan_id": execution_plan.plan_id}
        )
        
        # 2 판단 영역 표시용: 의도·추상계획·실행계획 요약 (Gemini Thoughts 스타일)
        thoughts = self._build_thoughts(user_intent, abstract_plan, execution_plan)
        return {**final_result, "thoughts": thoughts, "chat_only": False}
    
    def _analyze_user_intent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자 의도 분석
        
        간단한 규칙 기반 분석 (PoC 단계)
        실제 구현에서는 LLM 사용
        """
        input_data = payload.get("input_data", {})
        text = input_data.get("text", "").lower()
        has_image = input_data.get("has_image", False)
        
        # 의도 추론 (대화/일상 멘트 → 도구 실행 생략)
        conversation_phrases = (
            "대화", "잠깐", "이야기", "안녕", "뭐해", "뭐하네", "반가워",
            "놀자", "잡담", "채팅", "말해", "들어줘", "대해봐", "이야기하자"
        )
        execute_phrases = (
            "실행해줘", "실행 해줘", "진행해줘", "try-on", "try on",
            "입혀줘", "가상 피팅 실행", "실행해 주세요", "진행해 주세요"
        )
        # 정보성 질문(패션/RAG 설명 요청) → 도구 실행 없이 RAG로만 응답
        info_phrases = ("란 뭐야", "이 뭐야", "알려줘", "알려 주세요", "무엇", "어떤 내용", "뭐가 들어있", "설명해", "뭐예요", "무엇인가")
        if not has_image and any(p in text for p in conversation_phrases):
            intent_type = "conversation"
            run_try_on = False
        elif not has_image and any(p in text for p in info_phrases):
            intent_type = "information"
            run_try_on = False
        elif "추천" in text or "찾아줘" in text:
            intent_type = "garment_recommendation"
            run_try_on = True
        elif "입혀줘" in text or "가상 피팅" in text or has_image:
            intent_type = "3d_generation"
            run_try_on = has_image or any(p in text for p in execute_phrases)
        else:
            intent_type = "3d_generation"
            run_try_on = has_image or any(p in text for p in execute_phrases)
        
        return {
            "type": intent_type,
            "confidence": 0.9,
            "text": text,
            "has_image": has_image,
            "run_try_on": run_try_on,
        }
    
    def _respond_conversation(
        self,
        payload: Dict[str, Any],
        user_intent: Dict[str, Any],
        memory: ShortTermMemory,
        session_id: str
    ) -> Dict[str, Any]:
        """
        대화/일상 멘트에 대한 응답 (도구 호출 없음).
        OpenAI API가 동작하면 LLM 응답, 동작하지 않으면 기본 안내만 반환하며
        openai_used / openai_error 로 상태를 명시해 희망고문하지 않음.
        """
        user_text = (payload.get("input_data") or {}).get("text", "")
        def _norm_key(s):
            return (s or "").replace("\r", "").replace("\n", "").strip()
        api_key = _norm_key(os.environ.get("OpenAI_API_Key") or os.environ.get("OPENAI_API_KEY") or "")
        if not api_key:
            for k, v in os.environ.items():
                if v and "openai" in k.lower() and "key" in k.lower():
                    api_key = _norm_key(v)
                    break
        default_message = (
            "안녕하세요. 가상 피팅 도우미예요. "
            "옷 입혀달라거나 스타일 추천을 요청해 주시면 도와드릴게요."
        )
        message = default_message
        openai_used = False
        openai_error = None
        if not api_key:
            openai_error = "OpenAI API 키가 없습니다. .env 에 OpenAI_API_Key= 또는 OPENAI_API_KEY= 를 넣고 서버를 재시작해 주세요."
            print(f"[AgentRuntime] 대화: {openai_error}")
        elif not user_text:
            openai_error = "입력 내용이 없습니다."
        else:
            try:
                import requests
                print(f"[AgentRuntime] 대화 OpenAI 호출 시도 (입력 길이: {len(user_text)})")
                r = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": "당신은 가상 피팅 서비스의 친절한 도우미입니다. 한두 문장으로 짧게 대답하세요."},
                            {"role": "user", "content": user_text}
                        ],
                        "max_tokens": 150,
                    },
                    timeout=15,
                )
                if r.status_code == 200:
                    data = r.json()
                    choice = (data.get("choices") or [{}])[0]
                    msg = (choice.get("message") or {}).get("content", "").strip()
                    if msg:
                        message = msg
                        openai_used = True
                        print(f"[AgentRuntime] 대화 OpenAI 응답 사용 (길이: {len(message)})")
                    else:
                        openai_error = "OpenAI 응답에 메시지가 없습니다."
                else:
                    try:
                        err_json = r.json()
                        err_msg = err_json.get("error", {}).get("message", r.text[:200])
                    except Exception:
                        err_msg = (r.text or "")[:200]
                    openai_error = f"OpenAI API 오류 (HTTP {r.status_code}): {err_msg}"
                    print(f"[AgentRuntime] 대화 OpenAI 호출 실패: {openai_error}")
            except Exception as e:
                openai_error = f"OpenAI 호출 실패: {e!s}"
                import traceback
                print(f"[AgentRuntime] 대화 OpenAI 예외: {e}")
                traceback.print_exc()
        memory.add_conversation(
            user_input=user_text,
            agent_response=message,
            metadata={"intent": "conversation"}
        )
        thoughts = {
            "intent": {"type": "conversation", "reason": "도구 실행 없이 응답합니다."},
            "abstract_plan": None,
            "execution_plan": None,
        }
        return {
            "status": "completed",
            "message": message,
            "data": {},
            "steps": {},
            "final_result": {"status": "completed", "result": {"message": message}},
            "plan_id": None,
            "thoughts": thoughts,
            "openai_used": openai_used,
            "openai_error": openai_error,
        }
    
    def _respond_with_rag(
        self,
        payload: Dict[str, Any],
        memory: ShortTermMemory,
        session_id: str
    ) -> Dict[str, Any]:
        """정보성 질문: RAG 검색 결과로만 응답 (Try-On 실행 없음)."""
        user_text = (payload.get("input_data") or {}).get("text", "").strip()
        message = "검색된 참고 정보가 없습니다. 패션·의류·소재 관련 질문을 해 주세요."
        if self.rag_store and user_text:
            try:
                ctx = self.rag_store.get_context("garment_recommendation", user_text)
                suggestions = ctx.get("rag_suggestions") or []
                if suggestions:
                    parts = ["다음은 RAG에서 검색한 참고 정보입니다.\n"]
                    for i, s in enumerate(suggestions[:5], 1):
                        excerpt = (s[:400] + "…") if len(s) > 400 else s
                        parts.append(f"{i}. {excerpt}")
                    message = "\n\n".join(parts)
            except Exception as e:
                print(f"[AgentRuntime] RAG 응답 오류: {e}")
                message = "참고 정보 검색 중 오류가 났습니다. 잠시 후 다시 시도해 주세요."
        memory.add_conversation(user_input=user_text, agent_response=message, metadata={"intent": "information"})
        return {
            "status": "completed",
            "message": message,
            "data": {},
            "steps": {},
            "final_result": {"status": "completed", "result": {"message": message}},
            "plan_id": None,
            "thoughts": {
                "intent": {"type": "information", "reason": "RAG 검색 결과로 응답."},
                "abstract_plan": None,
                "execution_plan": None,
            },
        }

    def _respond_try_on_prompt(
        self,
        payload: Dict[str, Any],
        memory: ShortTermMemory,
        session_id: str
    ) -> Dict[str, Any]:
        """가상 피팅 의도지만 실행 요청 없을 때: RAG 검색 결과가 있으면 그대로 응답, 없으면 안내 문구."""
        user_text = (payload.get("input_data") or {}).get("text", "").strip()
        message = (
            "가상 피팅을 실행하려면 'Try-On 실행해줘' 또는 '입혀줘'라고 말씀해 주시거나, "
            "의류 이미지를 올린 뒤 보내기 해 주세요. 그때 하단에 완료 → 결과가 진행됩니다."
        )
        if self.rag_store and user_text:
            try:
                ctx = self.rag_store.get_context("garment_recommendation", user_text)
                suggestions = ctx.get("rag_suggestions") or []
                if suggestions:
                    parts = ["다음은 검색한 참고 정보입니다.\n"]
                    for i, s in enumerate(suggestions[:5], 1):
                        excerpt = (s[:400] + "…") if len(s) > 400 else s
                        parts.append(f"{i}. {excerpt}")
                    message = "\n\n".join(parts)
            except Exception as e:
                print(f"[AgentRuntime] RAG try_on_prompt 오류: {e}")
        memory.add_conversation(
            user_input=user_text,
            agent_response=message,
            metadata={"intent": "try_on_prompt"}
        )
        return {
            "status": "completed",
            "message": message,
            "data": {},
            "steps": {},
            "final_result": {"status": "completed", "result": {"message": message}},
            "plan_id": None,
            "thoughts": {
                "intent": {"type": "3d_generation", "reason": "실행 요청 없음 — 채팅만 응답."},
                "abstract_plan": None,
                "execution_plan": None,
            },
        }
    
    def _build_thoughts(
        self,
        user_intent: Dict[str, Any],
        abstract_plan: AbstractPlan,
        execution_plan: ExecutionPlan
    ) -> Dict[str, Any]:
        """판단 단계(2) 표시용: 의도·추상계획·실행계획 요약."""
        intent_type = user_intent.get("type", "")
        intent_labels = {
            "3d_generation": "가상 피팅(3D 생성)",
            "garment_recommendation": "의류 추천",
            "conversation": "대화",
            "information": "정보 검색(RAG)",
        }
        return {
            "intent": {
                "type": intent_type,
                "label": intent_labels.get(intent_type, intent_type),
                "has_image": user_intent.get("has_image", False),
                "text_preview": (user_intent.get("text") or "")[:80],
            },
            "abstract_plan": {
                "plan_type": abstract_plan.plan_type,
                "goal": abstract_plan.goal,
                "steps": abstract_plan.steps,
                "parameters": {k: v for k, v in (abstract_plan.parameters or {}).items() if v is not None},
            },
            "execution_plan": {
                "plan_id": execution_plan.plan_id,
                "steps": [
                    {
                        "step_id": s.get("step_id"),
                        "tool": s.get("tool"),
                        "action": s.get("action"),
                        "parameters": s.get("parameters"),
                    }
                    for s in execution_plan.steps
                ],
                "tools_required": execution_plan.tools_required,
            },
        }
    
    def _create_abstract_plan(
        self,
        user_intent: Dict[str, Any],
        payload: Dict[str, Any],
        memory: ShortTermMemory
    ) -> AbstractPlan:
        """
        추상적 작업 계획 수립 (Agent 1의 핵심 역할)
        
        큰 그림의 작업 계획을 생성
        """
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
        else:  # garment_recommendation
            return AbstractPlan(
                plan_type="garment_recommendation",
                goal="사용자 요청에 맞는 의상 추천",
                steps=[
                    "상품 검색",
                    "매칭 및 필터링",
                    "추천 결과 반환"
                ],
                parameters={
                    "query": payload.get("input_data", {}).get("text"),
                    "filters": {}
                },
                created_at=datetime.now().isoformat()
            )
    
    def _execute_plan(
        self,
        execution_plan: ExecutionPlan,
        memory: ShortTermMemory
    ) -> Dict[str, Any]:
        """
        실행 계획에 따라 도구 실행
        
        순차적으로 각 단계를 실행하고 결과를 수집
        """
        results = {}
        execution_context = {}
        
        # 단계별 실행 (의존성 고려)
        print(f"[AgentRuntime._execute_plan] 총 {len(execution_plan.steps)}개 단계 실행 시작")
        for step_idx, step in enumerate(execution_plan.steps, 1):
            step_id = step["step_id"]
            tool_name = step["tool"]
            action = step["action"]
            parameters = step.get("parameters", {})
            dependencies = step.get("dependencies", [])
            print(f"[AgentRuntime._execute_plan] 단계 {step_idx}/{len(execution_plan.steps)}: {tool_name}.{action} (step_id={step_id})")
            
            # 의존성 확인
            if dependencies:
                # 의존성 결과를 파라미터에 포함
                for dep_id in dependencies:
                    if dep_id in results:
                        # results[dep_id]는 {"status": "success", "result": {...}, "step_id": ...} 구조
                        # 실제 결과는 "result" 키에 있음
                        dep_result = results[dep_id]
                        if isinstance(dep_result, dict) and "result" in dep_result:
                            parameters["_dependency_result"] = dep_result["result"]
                        else:
                            parameters["_dependency_result"] = dep_result
            
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
                except Exception as e:
                    print(f"[AgentRuntime._execute_plan] 도구 실행 오류: {tool_name}.{action} - {str(e)}")
                    import traceback
                    traceback.print_exc()
                    results[step_id] = {
                        "status": "error",
                        "error": str(e),
                        "step_id": step_id
                    }
            else:
                results[step_id] = {
                    "status": "error",
                    "error": f"Tool '{tool_name}' not found",
                    "step_id": step_id
                }
        
        # 최종 결과 반환
        final_result_id = max([s["step_id"] for s in execution_plan.steps])
        final_result = results.get(final_result_id, {})
        
        return {
            "status": "completed",
            "plan_id": execution_plan.plan_id,
            "steps": results,
            "final_result": final_result,
            "all_results": results
        }
    
    def _self_correction_loop(
        self,
        execution_plan: ExecutionPlan,
        execution_result: Dict[str, Any],
        memory: ShortTermMemory,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        자기 수정 루프 (Self-Correction Loop)
        
        결과를 평가하고, 실패 시 재시도
        PoC 단계에서는 단순 재시도만 수행
        """
        # 결과 평가
        evaluation = self._evaluate_result(execution_result)
        
        if evaluation["success"]:
            return {
                "status": "success",
                "message": "작업이 성공적으로 완료되었습니다.",
                "data": execution_result,
                "evaluation": evaluation
            }
        
        # 의류 이미지 없음 등 재시도해도 바뀌지 않는 오류는 재시도하지 않고 바로 실패 메시지 반환
        step_error = evaluation.get("step_error_message") or ""
        if "의류 이미지" in step_error or "image_path" in step_error.lower():
            return {
                "status": "failed",
                "message": "의류 이미지를 첨부한 뒤 '입혀줘' 또는 'Try-On 실행해줘'로 다시 시도해 주세요.",
                "data": execution_result,
                "evaluation": evaluation
            }
        
        # 실패 시 재시도
        if retry_count < self.max_retries:
            # 계획 수정 (간단한 재시도)
            retry_result = self._execute_plan(execution_plan, memory)
            return self._self_correction_loop(
                execution_plan,
                retry_result,
                memory,
                retry_count + 1
            )
        else:
            return {
                "status": "failed",
                "message": "최대 재시도 횟수에 도달했습니다.",
                "data": execution_result,
                "evaluation": evaluation
            }
    
    def _evaluate_result(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        결과 평가
        
        PoC 단계에서는 성공/실패만 판단
        """
        all_steps = execution_result.get("all_results", {})
        final_result = execution_result.get("final_result", {})
        
        # 실행 결과 자체의 상태 확인
        execution_status = execution_result.get("status", "unknown")
        
        # 모든 단계가 성공했는지 확인 (단계 실행 성공 + result 내부 status가 error가 아님)
        failed_steps = []
        step_error_message = None
        for step_id, result in all_steps.items():
            if isinstance(result, dict):
                step_status = result.get("status", "unknown")
                inner = result.get("result") if isinstance(result.get("result"), dict) else {}
                inner_status = inner.get("status", "")
                if step_status not in ["success", "completed"] or inner_status == "error":
                    failed_steps.append(step_id)
                    if inner.get("message") and not step_error_message:
                        step_error_message = inner.get("message")
            else:
                failed_steps.append(step_id)
        
        # 최종 결과도 확인
        if isinstance(final_result, dict):
            final_inner = final_result.get("result") if isinstance(final_result.get("result"), dict) else {}
            final_status = final_result.get("status", "unknown")
            if final_inner.get("status") == "error" and final_inner.get("message"):
                step_error_message = step_error_message or final_inner.get("message")
            if final_status not in ["success", "completed"] or final_inner.get("status") == "error":
                success = False
            else:
                success = len(failed_steps) == 0 and execution_status == "completed"
        else:
            success = len(failed_steps) == 0 and execution_status == "completed"
        
        return {
            "success": success,
            "failed_steps": failed_steps,
            "total_steps": len(all_steps),
            "successful_steps": len(all_steps) - len(failed_steps),
            "execution_status": execution_status,
            "step_error_message": step_error_message,
        }



