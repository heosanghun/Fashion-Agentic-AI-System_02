"""
OpenAI API 키 구동 확인 테스트
.env 의 OpenAI_API_Key 로드 여부와 API 호출 가능 여부만 확인합니다.
(결제 미연결 시 API 오류가 나올 수 있음 — 테스트 목적)
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def main():
    print("=" * 50)
    print("OpenAI API 키 구동 확인 테스트")
    print("=" * 50)

    # 1) .env 로드 (dotenv + 실패 시 직접 파싱)
    env_path = project_root / ".env"
    if not env_path.exists():
        print(f"[경고] .env 없음: {env_path}")
    else:
        print(f"[OK] .env 파일 있음: {env_path}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, encoding="utf-8")
        except ImportError:
            pass
        # dotenv만으로는 안 읽힐 수 있으므로 직접 파싱 보조
        raw = env_path.read_text(encoding="utf-8-sig").strip()  # BOM 제거
        if not raw:
            print("  [안내] .env 파일이 비어 있습니다. Cursor에서 .env를 저장(Ctrl+S)한 뒤 다시 실행하세요.")
        for line in raw.splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k and v:
                    os.environ[k] = v
                    if "openai" in k.lower() or "api_key" in k.lower():
                        print(f"  - 환경 변수 로드: {k} (길이 {len(v)})")

    # 2) 키 확인 (OpenAI_API_Key / OPENAI_API_KEY 둘 다 허용)
    api_key = os.environ.get("OpenAI_API_Key") or os.environ.get("OPENAI_API_KEY") or ""
    api_key = api_key.strip()

    if not api_key:
        print("[실패] OpenAI API 키가 없습니다.")
        print("  - .env 에 OpenAI_API_Key=키값 또는 OPENAI_API_KEY=키값 을 넣고, 파일을 저장한 뒤 다시 실행하세요.")
        return 1

    print(f"[OK] API 키 로드됨 (길이: {len(api_key)} 문자)")
    print()

    # 3) API 호출 테스트 (최소한의 요청 — 결제 미연결이면 오류 메시지로 확인)
    print("OpenAI API 호출 테스트 (최소 요청)...")
    try:
        import urllib.request
        import json

        url = "https://api.openai.com/v1/models"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", f"Bearer {api_key}")

        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode())
            models = data.get("data", [])[:3]
            print("[OK] API 연결 성공 (키 유효)")
            if models:
                print("  - 사용 가능한 모델 예시:", [m.get("id") for m in models])
            else:
                print("  - 모델 목록 응답 수신됨")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"[API 응답] HTTP {e.code}: {e.reason}")
        try:
            j = json.loads(body) if body else {}
            err = j.get("error", {})
            msg = err.get("message", body[:200] if body else "")
            print(f"  - 메시지: {msg}")
        except Exception:
            print(f"  - 본문: {body[:300]}")
        if e.code == 401:
            print("  → 키가 잘못되었거나 만료됨")
        elif e.code == 429:
            print("  → 사용량/결제 제한 (결제 미연결일 수 있음)")
        else:
            print("  → 결제 미연결 등으로 거절되었을 수 있음 (테스트만 진행한 상태)")
    except Exception as e:
        print(f"[오류] {type(e).__name__}: {e}")

    print()
    print("테스트 완료.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
