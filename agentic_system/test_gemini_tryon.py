"""
Gemini Try-On 직접 호출 테스트 (로컬)
- .env의 GEMINI_API_KEY 로드
- 의류/인물 이미지 경로로 try_on 호출
- 콘솔에 결과 및 로그 출력
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agentic_system"))

# .env 로드
_env = project_root / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env, encoding="utf-8-sig")
    except Exception as e:
        print(f"dotenv 로드 실패: {e}")

key = os.environ.get("GEMINI_API_KEY", "").strip()
print(f"[테스트] GEMINI_API_KEY 존재: {bool(key)}, 길이: {len(key)}")

# 업로드 폴더에서 샘플 이미지 (의류 1, 인물 1)
uploads = project_root / "uploads"
garment = None
person = None
for f in uploads.iterdir() if uploads.exists() else []:
    if "28.jpg" in f.name:
        garment = f
    if "1995113" in f.name or "무제" in f.name or "person" in f.name.lower():
        person = f
    if garment and person:
        break
# 없으면 outputs/renders 기존 파일이나 첫 두 이미지 사용
if not garment and uploads.exists():
    for f in sorted(uploads.iterdir())[:2]:
        if garment is None:
            garment = f
        else:
            person = f
            break

if not garment or not person:
    print("[테스트] 업로드 폴더에 이미지 2개 필요. garment:", garment, "person:", person)
    sys.exit(1)

print("[테스트] 의류:", garment, "인물:", person)

# Try-On 도구 호출
from agentic_system.tools.gemini_tryon import gemini_tryon_tool

context = {
    "image_path": str(garment),
    "person_image_path": str(person),
    "text": "입혀줘",
}
result = gemini_tryon_tool("try_on", {}, context)
print("[테스트] 결과 status:", result.get("status"))
print("[테스트] 결과 message:", result.get("message"))
print("[테스트] 결과 image_path:", result.get("image_path"))
if result.get("note"):
    print("[테스트] note:", result.get("note"))
