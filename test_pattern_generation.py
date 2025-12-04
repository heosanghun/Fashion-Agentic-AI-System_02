"""
패턴 파일 생성 직접 테스트
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agentic_system"))

from agentic_system.tools.extensions import Extensions2DTo3D

# Mock 패턴 생성 테스트
tool = Extensions2DTo3D()

# Mock 분석 결과
mock_analysis = {
    "status": "success",
    "analysis": {
        "garment_type": "상의",
        "style": "캐주얼",
        "color": "검정색",
        "type": "hoodie"
    },
    "image_path": "test.jpg",
    "message": "이미지 분석이 완료되었습니다. (Mock 모드)"
}

print("=" * 60)
print("Mock 패턴 생성 테스트")
print("=" * 60)

# 패턴 생성
result = tool._mock_generate_pattern(mock_analysis)

print(f"\n결과:")
print(f"  상태: {result.get('status')}")
print(f"  패턴 경로: {result.get('pattern_path')}")

# 파일 존재 확인
pattern_path = Path(result.get('pattern_path'))
if pattern_path.exists():
    print(f"  ✓ 파일 존재 확인: {pattern_path}")
    print(f"  파일 크기: {pattern_path.stat().st_size} bytes")
    
    # 파일 내용 확인
    import json
    with open(pattern_path, 'r', encoding='utf-8') as f:
        pattern_data = json.load(f)
    print(f"  파일 내용 확인:")
    print(f"    garment_type: {pattern_data.get('garment_type')}")
    print(f"    components: {pattern_data.get('components')}")
else:
    print(f"  ❌ 파일이 존재하지 않습니다: {pattern_path}")

print("\n" + "=" * 60)

