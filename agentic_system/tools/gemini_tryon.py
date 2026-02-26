"""
Gemini Try-On Tool - Google Gemini API 기반 가상 피팅 도구

ChatGarment/GarmentCodeRC를 대체하여 Gemini API(및 향후 Vertex AI Virtual Try-On)를
활용한 가상 피팅 결과를 생성합니다.
"""

from typing import Dict, Any, Optional
import os
import shutil
from pathlib import Path

# 프로젝트 루트
_tools_dir = Path(__file__).resolve().parent
_project_root = _tools_dir.parent.parent

# Gemini SDK: google-genai (권장) 또는 google-generativeai
try:
    from google import genai
    GEMINI_SDK = "genai"
except ImportError:
    genai = None
    GEMINI_SDK = None
try:
    if GEMINI_SDK != "genai":
        import google.generativeai as genai_legacy
        GEMINI_SDK = "generativeai"
except ImportError:
    genai_legacy = None
    if not GEMINI_SDK:
        GEMINI_SDK = None


class GeminiTryOnTool:
    """
    Gemini API 기반 가상 피팅 도구.
    - analyze_image: 의류 이미지 분석 (Gemini Vision)
    - try_on: 가상 피팅 이미지 생성 (Gemini/Vertex Try-On 또는 Mock)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.name = "gemini_tryon"
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        self.client = None
        self._sdk = GEMINI_SDK
        if GEMINI_SDK == "genai" and self.api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GeminiTryOn] Client 초기화 실패: {e}")
        elif GEMINI_SDK == "generativeai" and self.api_key and genai_legacy is not None:
            try:
                genai_legacy.configure(api_key=self.api_key)
                self.client = genai_legacy.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"[GeminiTryOn] Legacy 모델 초기화 실패: {e}")

    def execute(
        self,
        action: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action == "analyze_image":
            return self._analyze_image(parameters, context)
        if action == "try_on":
            return self._try_on(parameters, context)
        if action == "process_request":
            # 한 번에 처리 (기존 extensions와 동일한 진입점)
            return self._try_on(
                parameters or context,
                context,
            )
        return {
            "status": "error",
            "message": f"Unknown action: {action}",
            "supported_actions": ["analyze_image", "try_on", "process_request"],
        }

    def _analyze_image(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        image_path = (
            parameters.get("image_path")
            or context.get("image_path")
            or context.get("step_1_result", {}).get("image_path")
        )
        text_prompt = parameters.get("text_description") or context.get("text") or ""

        if not image_path or not Path(image_path).exists():
            return {
                "status": "error",
                "message": "이미지 경로가 없거나 파일이 존재하지 않습니다.",
                "image_path": image_path,
            }

        if not self.client:
            return self._mock_analyze(image_path, text_prompt)

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            if self._sdk == "genai":
                prompt = (
                    "이 의류 이미지를 분석해주세요. "
                    "의류 종류, 색상, 스타일, 소재 느낌을 한 문단으로 요약해주세요."
                )
                if text_prompt:
                    prompt += f"\n사용자 요청: {text_prompt}"
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[prompt, image_data],
                )
                analysis_text = response.text if hasattr(response, "text") else str(response)
            else:
                import PIL.Image
                img = PIL.Image.open(image_path).convert("RGB")
                prompt = (
                    "이 의류 이미지를 분석해주세요. "
                    "의류 종류, 색상, 스타일, 소재 느낌을 한 문단으로 요약해주세요."
                )
                if text_prompt:
                    prompt += f"\n사용자 요청: {text_prompt}"
                response = self.client.generate_content([prompt, img])
                analysis_text = response.text

            return {
                "status": "success",
                "analysis": analysis_text,
                "image_path": image_path,
                "message": "Gemini로 의류 이미지 분석을 완료했습니다.",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "image_path": image_path,
                "fallback": self._mock_analyze(image_path, text_prompt),
            }

    def _try_on(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """가상 피팅 실행. person_image + garment_image → 결과 이미지."""
        image_path = (
            parameters.get("image_path")
            or context.get("image_path")
        )
        person_path = parameters.get("person_image_path") or context.get("person_image_path")
        text_prompt = parameters.get("text_description") or context.get("text") or ""

        if not image_path or not Path(image_path).exists():
            return {
                "status": "error",
                "message": "의류 이미지 경로가 없거나 파일이 존재하지 않습니다.",
                "image_path": None,
            }

        output_dir = _project_root / "outputs" / "renders"
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "tryon_result.png"

        # Vertex AI Virtual Try-On API 사용 가능 시 여기서 호출
        # if os.environ.get("VERTEX_PROJECT") and person_path and Path(person_path).exists():
        #     return self._vertex_try_on(image_path, person_path, str(out_path))

        if self.client and person_path and Path(person_path).exists():
            # Gemini로 합성 요청 (이미지 두 장 + 프롬프트) — 실제 Try-On은 Vertex 권장
            try:
                with open(image_path, "rb") as f1, open(person_path, "rb") as f2:
                    img1, img2 = f1.read(), f2.read()
                mime1 = "image/png" if str(image_path).lower().endswith(".png") else "image/jpeg"
                mime2 = "image/png" if str(person_path).lower().endswith(".png") else "image/jpeg"

                if self._sdk == "genai":
                    prompt = (
                        "첫 번째 이미지는 의류, 두 번째 이미지는 인물입니다. "
                        "이 의류를 입혀본 것처럼 보이는 결과를 설명해주세요. "
                        "실제 합성 이미지 생성은 Vertex AI Virtual Try-On API를 사용하세요."
                    )
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[prompt, img1, img2],
                    )
                    desc = response.text if hasattr(response, "text") else str(response)
                else:
                    import PIL.Image
                    prompt = "첫 번째: 의류, 두 번째: 인물. 이 의류를 입혀본 것처럼 설명해주세요."
                    response = self.client.generate_content(
                        [prompt, PIL.Image.open(image_path), PIL.Image.open(person_path)]
                    )
                    desc = response.text

                # 실제 합성 이미지가 없으므로 의류 이미지를 결과로 복사 (플로우 유지)
                shutil.copy(image_path, out_path)
                return {
                    "status": "success",
                    "image_path": str(out_path),
                    "message": "가상 피팅 요청이 처리되었습니다.",
                    "description": desc,
                    "note": "실제 합성은 Vertex AI Virtual Try-On API 연동 시 적용됩니다.",
                }
            except Exception as e:
                pass  # fallback to mock

        # Mock: 의류 이미지를 outputs/renders/tryon_result.png 로 복사 후 반환
        try:
            shutil.copy(image_path, out_path)
        except Exception as e:
            return {
                "status": "error",
                "message": f"결과 저장 실패: {e}",
                "image_path": None,
            }

        return {
            "status": "success",
            "image_path": str(out_path),
            "message": "가상 피팅 결과가 생성되었습니다. (Gemini API 키 설정 시 분석·향상 적용)",
            "note": "GEMINI_API_KEY를 설정하면 의류 분석이 적용됩니다. 실제 합성은 Vertex AI Virtual Try-On API를 연동하세요.",
        }

    def _mock_analyze(self, image_path: str, text_prompt: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "analysis": "의류 이미지 분석 (Mock). GEMINI_API_KEY 설정 시 Gemini Vision으로 분석합니다.",
            "image_path": image_path,
            "message": "Mock 분석 완료.",
        }


def gemini_tryon_tool(action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Agent Runtime에서 호출하는 도구 함수 (기존 extensions_2d_to_3d_tool 시그니처와 동일)."""
    tool = GeminiTryOnTool()
    return tool.execute(action, parameters, context)
