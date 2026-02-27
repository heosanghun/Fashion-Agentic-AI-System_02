"""
Gemini Try-On Tool - Google Gemini API 기반 가상 피팅 도구

ChatGarment/GarmentCodeRC를 대체하여 Gemini API(및 향후 Vertex AI Virtual Try-On)를
활용한 가상 피팅 결과를 생성합니다.
"""

from typing import Dict, Any, Optional
import os
import shutil
import base64
from pathlib import Path

try:
    import urllib.request
    _urllib_available = True
except ImportError:
    _urllib_available = False
try:
    import requests
    _requests_available = True
except ImportError:
    _requests_available = False
try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    fal_client = None
    FAL_AVAILABLE = False

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

    def _fal_try_on(
        self,
        person_path: str,
        garment_path: str,
        out_path: Path,
    ) -> Optional[Dict[str, Any]]:
        """fal.ai Virtual Try-On API로 합성 이미지 생성. FAL_KEY 필요."""
        if not FAL_AVAILABLE or fal_client is None:
            return None
        try:
            with open(person_path, "rb") as f1, open(garment_path, "rb") as f2:
                person_b = f1.read()
                garment_b = f2.read()
            mime_p = "image/png" if str(person_path).lower().endswith(".png") else "image/jpeg"
            mime_g = "image/png" if str(garment_path).lower().endswith(".png") else "image/jpeg"
            person_uri = "data:{};base64,{}".format(mime_p, base64.b64encode(person_b).decode("ascii"))
            garment_uri = "data:{};base64,{}".format(mime_g, base64.b64encode(garment_b).decode("ascii"))

            result = fal_client.subscribe(
                "fal-ai/image-apps-v2/virtual-try-on",
                arguments={
                    "person_image_url": person_uri,
                    "clothing_image_url": garment_uri,
                },
            )
            images = result.get("images") if isinstance(result, dict) else getattr(result, "images", None) or []
            if not images:
                return None
            url = images[0].get("url") if isinstance(images[0], dict) else getattr(images[0], "url", None)
            if not url:
                return None
            # 다운로드하여 저장
            if _requests_available:
                resp = requests.get(url, timeout=60)
                resp.raise_for_status()
                with open(out_path, "wb") as f:
                    f.write(resp.content)
            elif _urllib_available:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    with open(out_path, "wb") as f:
                        f.write(resp.read())
            else:
                return None
            return {
                "status": "success",
                "image_path": str(out_path),
                "message": "가상 피팅 합성 이미지가 생성되었습니다. (fal.ai Virtual Try-On)",
            }
        except Exception as e:
            print(f"[GeminiTryOn] fal.ai Try-On 실패: {e}")
            return None

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
        print(f"[GeminiTryOn] try_on 진입: image_path={bool(image_path)}, person_path={bool(person_path)}, client={self.client is not None}")

        if not image_path or not Path(image_path).exists():
            return {
                "status": "error",
                "message": "입을 옷 사진(의류 이미지)을 올려주세요. 가상 피팅은 '의류 사진' + '내 사진(인물)' 두 장을 올리면 더 정확합니다.",
                "image_path": None,
            }

        output_dir = _project_root / "outputs" / "renders"
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "tryon_result.png"

        # 1) Gemini Try-On 우선 (SIMS Fashion 등과 동일한 GEMINI_API_KEY 사용)
        if self.client and person_path and Path(person_path).exists():
            # Gemini 이미지 생성으로 Try-On 합성 시도 (google-genai)
            try:
                with open(image_path, "rb") as f1, open(person_path, "rb") as f2:
                    img1, img2 = f1.read(), f2.read()
                mime1 = "image/png" if str(image_path).lower().endswith(".png") else "image/jpeg"
                mime2 = "image/png" if str(person_path).lower().endswith(".png") else "image/jpeg"

                if self._sdk == "genai":
                    from google.genai import types
                    prompt = (
                        "첫 번째 이미지는 입을 옷(의류) 사진이고, 두 번째 이미지는 그 옷을 입을 사람(인물) 사진입니다. "
                        "두 번째 이미지의 인물이 첫 번째 이미지의 옷을 입은 모습으로, 한 장의 자연스러운 합성 사진을 생성해주세요. "
                        "인물의 포즈와 얼굴은 유지하고, 옷만 정확히 입혀서 사실적으로 보이게 해주세요."
                    )
                    contents = [
                        prompt,
                        types.Part.from_bytes(data=img1, mime_type=mime1),
                        types.Part.from_bytes(data=img2, mime_type=mime2),
                    ]
                    # 이미지 생성 지원 모델: exp 또는 preview
                    for model_id in ("gemini-2.0-flash-exp-image-generation", "gemini-2.0-flash-preview-image-generation", "gemini-2.5-flash-preview-image-generation"):
                        try:
                            print(f"[GeminiTryOn] Gemini 이미지 생성 호출 중 ({model_id})...")
                            response = self.client.models.generate_content(
                                model=model_id,
                                contents=contents,
                                config=types.GenerateContentConfig(
                                    response_modalities=["Text", "Image"],
                                ),
                            )
                        except Exception as model_err:
                            print(f"[GeminiTryOn] 모델 {model_id} 실패: {model_err}")
                            continue
                        desc = ""
                        image_saved = False
                        # 새 SDK: response.parts / 기존: response.candidates[0].content.parts
                        parts = []
                        if getattr(response, "parts", None):
                            parts = list(response.parts)
                        elif response.candidates and getattr(response.candidates[0], "content", None) and getattr(response.candidates[0].content, "parts", None):
                            parts = list(response.candidates[0].content.parts)
                        for i, part in enumerate(parts):
                            if getattr(part, "text", None):
                                desc = (part.text or "")[:500]
                                print(f"[GeminiTryOn] 응답 텍스트 파트 {i}: {desc[:200]}...")
                            # 이미지: inline_data.data 또는 as_image() (PIL)
                            blob = None
                            if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                                blob = part.inline_data.data
                            elif getattr(part, "as_image", None):
                                try:
                                    pil_img = part.as_image()
                                    if pil_img is not None:
                                        import io
                                        buf = io.BytesIO()
                                        pil_img.save(buf, format="PNG")
                                        blob = buf.getvalue()
                                except Exception:
                                    pass
                            if blob:
                                with open(out_path, "wb") as f:
                                    f.write(blob)
                                image_saved = True
                                print(f"[GeminiTryOn] 이미지 파트 저장 완료: {out_path}")
                                break
                        if not image_saved:
                            print(f"[GeminiTryOn] 응답에 이미지 파트 없음 (parts 수: {len(parts)}). 다음 모델 시도 또는 fallback.")
                        if image_saved:
                            break
                    if image_saved:
                        return {
                            "status": "success",
                            "image_path": str(out_path),
                            "message": "가상 피팅 결과 이미지가 생성되었습니다.",
                            "description": desc or "Gemini 이미지 생성으로 합성되었습니다.",
                        }
                    # Gemini에서 이미지 미반환 시 fal.ai 시도 (FAL_KEY 있을 때만)
                    if os.environ.get("FAL_KEY"):
                        fal_result = self._fal_try_on(person_path, image_path, out_path)
                        if fal_result is not None:
                            return fal_result
                else:
                    import PIL.Image
                    prompt = "첫 번째: 의류, 두 번째: 인물. 이 의류를 입혀본 것처럼 설명해주세요."
                    response = self.client.generate_content(
                        [prompt, PIL.Image.open(image_path), PIL.Image.open(person_path)]
                    )
                    desc = response.text
            except Exception as e:
                print(f"[GeminiTryOn] 이미지 생성 실패 (fallback): {e}")
                desc = str(e)

            # 2) 이미지 생성 실패 시 — 의류 이미지는 표시하지 않고 안내만 (옷만 나오지 않게)
            return {
                "status": "success",
                "image_path": None,
                "message": "가상 피팅 합성 이미지가 생성되지 않았습니다. 같은 의류·인물로 다시 시도하거나, GEMINI_API_KEY·이미지 생성 모델 지원 여부를 확인해 주세요.",
                "description": desc or "",
                "garment_only_fallback": True,
            }

        # 인물 사진 없음 — 결과 이미지로 옷만 보이지 않게 image_path=None
        return {
            "status": "success",
            "image_path": None,
            "message": "의류 사진과 내 사진(인물) 두 장을 올린 뒤 '입혀줘'를 보내주시면 가상 피팅 합성이 진행됩니다.",
            "note": "GEMINI_API_KEY를 설정하고 의류+인물 두 장을 올려주세요.",
            "garment_only_fallback": True,
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
