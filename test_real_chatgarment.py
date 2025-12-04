#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 ChatGarment 모델로 이미지 테스트
"""

import sys
import time
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agentic_system"))

def test_real_chatgarment():
    """실제 ChatGarment 모델로 이미지 분석 테스트"""
    print("=" * 80)
    print("실제 ChatGarment 모델 테스트")
    print("=" * 80)
    
    # Extensions2DTo3D 초기화 및 모델 로딩
    print("\n[1] Extensions2DTo3D 초기화 및 모델 로딩")
    print("-" * 80)
    
    try:
        from agentic_system.tools.extensions import Extensions2DTo3D
        tool = Extensions2DTo3D()
        print("✅ Extensions2DTo3D 초기화 성공")
        
        # 모델 로딩
        print("\n모델 로딩 중...")
        tool._load_model()
        
        if not tool.model_loaded:
            print("❌ 모델 로딩 실패")
            return False
        
        print("✅ 모델 로딩 성공!")
        print(f"   모델 타입: {type(tool.model).__name__}")
        print(f"   모델 디바이스: {tool.model.device if hasattr(tool.model, 'device') else 'N/A'}")
        
    except Exception as e:
        print(f"❌ 초기화 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 이미지 경로 확인
    print("\n[2] 이미지 파일 확인")
    print("-" * 80)
    
    image_path = project_root / "image" / "TShirt.jpg"
    if not image_path.exists():
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return False
    
    print(f"✅ 이미지 파일 확인: {image_path}")
    print(f"   파일 크기: {image_path.stat().st_size / 1024:.2f} KB")
    
    # 실제 이미지 분석 테스트
    print("\n[3] 실제 이미지 분석 테스트")
    print("-" * 80)
    
    try:
        print("이미지 분석 시작...")
        start_time = time.time()
        
        # analyze_image 액션 실행
        result = tool.execute(
            action="analyze_image",
            parameters={
                "image_path": str(image_path),
                "text_description": "이 티셔츠를 분석해주세요"
            },
            context={}
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ 이미지 분석 완료 (소요 시간: {elapsed_time:.2f}초)")
        print(f"   상태: {result.get('status', 'N/A')}")
        
        if result.get('status') == 'success':
            print("✅ 실제 ChatGarment 모델이 이미지를 분석했습니다!")
            
            # 분석 결과 확인
            analysis = result.get('analysis', {})
            if analysis:
                print(f"\n분석 결과 키: {list(analysis.keys())}")
                print(f"분석 결과 타입: {type(analysis)}")
                
                # JSON으로 출력 (일부만)
                import json
                analysis_str = json.dumps(analysis, indent=2, ensure_ascii=False)
                if len(analysis_str) > 500:
                    print(f"\n분석 결과 (처음 500자):\n{analysis_str[:500]}...")
                else:
                    print(f"\n분석 결과:\n{analysis_str}")
            
            return True
        else:
            print(f"❌ 이미지 분석 실패: {result.get('message', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"❌ 이미지 분석 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    success = test_real_chatgarment()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 테스트 성공!")
        print("   실제 ChatGarment 모델이 정상적으로 동작합니다.")
    else:
        print("❌ 테스트 실패")
        print("   모델 로딩 또는 이미지 분석에 문제가 있습니다.")
    print("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

