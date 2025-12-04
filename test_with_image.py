#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
제공된 이미지로 ChatGarment 시스템 테스트
"""

import sys
import time
import requests
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agentic_system"))

def test_with_image(image_path):
    """제공된 이미지로 API 요청 테스트"""
    print("=" * 60)
    print("ChatGarment 시스템 - 이미지 테스트")
    print("=" * 60)
    
    # 이미지 파일 확인
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return False
    
    print(f"✅ 이미지 파일 확인: {image_file}")
    print(f"   파일 크기: {image_file.stat().st_size / 1024:.2f} KB")
    
    # API 서버 확인
    print("\nAPI 서버 연결 확인 중...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ API 서버가 실행 중이지 않습니다.")
            print("   먼저 API 서버를 시작하세요: python -m uvicorn agentic_system.api.main:app --port 8000")
            return False
        print("✅ API 서버 연결 성공")
    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("   먼저 API 서버를 시작하세요: python -m uvicorn agentic_system.api.main:app --port 8000")
        return False
    
    # 이미지 업로드 및 요청
    print("\n" + "=" * 60)
    print("이미지 업로드 및 처리 요청")
    print("=" * 60)
    
    try:
        session_id = f"test_{int(time.time())}"
        
        print(f"세션 ID: {session_id}")
        print(f"이미지 경로: {image_path}")
        print("요청 전송 중...")
        
        with open(image_file, 'rb') as f:
            files = {
                "image": (image_file.name, f, "image/jpeg")
            }
            data = {
                "text": "이 폴로 셔츠를 3D로 만들어줘",
                "session_id": session_id
            }
            
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/api/v1/request",
                files=files,
                data=data,
                timeout=120
            )
            elapsed_time = time.time() - start_time
        
        print(f"\n✅ 요청 완료 (소요 시간: {elapsed_time:.2f}초)")
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n" + "=" * 60)
            print("처리 결과")
            print("=" * 60)
            print(f"상태: {result.get('status', 'N/A')}")
            print(f"메시지: {result.get('message', 'N/A')}")
            
            # 결과 데이터 확인
            data = result.get('data', {})
            if data:
                print(f"\n결과 데이터 키: {list(data.keys())}")
                
                # 출력 파일 경로 확인
                if 'output_files' in data:
                    print("\n생성된 파일:")
                    for key, path in data['output_files'].items():
                        file_path = Path(path)
                        if file_path.exists():
                            print(f"  ✅ {key}: {path} ({file_path.stat().st_size / 1024:.2f} KB)")
                        else:
                            print(f"  ⚠️  {key}: {path} (파일 없음)")
                
                # final_result 확인
                if 'final_result' in data:
                    final_result = data['final_result']
                    print(f"\n최종 결과:")
                    print(f"  상태: {final_result.get('status', 'N/A')}")
                    if 'output_files' in final_result:
                        print(f"  출력 파일:")
                        for key, path in final_result['output_files'].items():
                            file_path = Path(path)
                            if file_path.exists():
                                print(f"    ✅ {key}: {path}")
                            else:
                                print(f"    ⚠️  {key}: {path} (파일 없음)")
            
            return True
        else:
            print(f"\n❌ 요청 실패: {response.status_code}")
            print(f"응답: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    # 실제 파일명 확인 (TShirt.jpg 또는 @TShirt.jpg)
    image_paths = [
        r"D:\AI\ChatGarment\image\TShirt.jpg",
        r"D:\AI\ChatGarment\image\@TShirt.jpg"
    ]
    
    image_path = None
    for path in image_paths:
        if Path(path).exists():
            image_path = path
            break
    
    if not image_path:
        print("❌ 이미지 파일을 찾을 수 없습니다.")
        print(f"   확인한 경로: {image_paths}")
        return 1
    
    print("\n" + "=" * 60)
    print("ChatGarment 시스템 - 이미지 테스트")
    print("=" * 60)
    print(f"테스트 이미지: {image_path}")
    print("=" * 60 + "\n")
    
    success = test_with_image(image_path)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 테스트 성공!")
    else:
        print("❌ 테스트 실패")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

