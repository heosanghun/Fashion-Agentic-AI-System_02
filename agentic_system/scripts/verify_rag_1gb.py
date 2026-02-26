"""
로컬 RAG 1GB 셀프점검·검증
실행: python -m agentic_system.scripts.verify_rag_1gb
"""
from pathlib import Path

AGENTIC_ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = AGENTIC_ROOT / "data" / "rag_fashion_1gb"
MAX_BYTES = 1 * 1024 * 1024 * 1024  # 1GB

def main():
    if not TARGET_DIR.exists():
        print(f"[검증] 폴더 없음: {TARGET_DIR}")
        return False
    total = sum(f.stat().st_size for f in TARGET_DIR.glob("*.txt") if f.is_file())
    count = len(list(TARGET_DIR.glob("*.txt")))
    ok = total >= MAX_BYTES
    print(f"[검증] 폴더: {TARGET_DIR}")
    print(f"[검증] 파일 수: {count}")
    print(f"[검증] 총 용량: {total:,} bytes ({total/(1024*1024):.2f} MB = {total/(1024**3):.2f} GB)")
    print(f"[검증] 1GB 도달: {'예' if ok else '아니오 (부족)'}")
    return ok

if __name__ == "__main__":
    main()
