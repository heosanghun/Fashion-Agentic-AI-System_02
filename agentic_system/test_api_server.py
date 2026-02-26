#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 서버 테스트 스크립트
프론트엔드에서 실제로 작동하는지 확인
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import json
from pathlib import Path

def test_api_health():
    """헬스체크 테스트"""
    print("=" * 60)
    print("1. API 헬스체크 테스트")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API 서버 정상 작동")
            print(f"   응답: {response.json()}")
            return True
        else:
            print(f"❌ API 서버 오류: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("   서버가 실행 중인지 확인: uvicorn api.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def test_api_root():
    """루트 엔드포인트 테스트"""
    print("\n" + "=" * 60)
    print("2. 루트 엔드포인트 테스트")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ 루트 엔드포인트 정상")
            print(f"   응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 루트 엔드포인트 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def test_text_request():
    """텍스트 요청 테스트"""
    print("\n" + "=" * 60)
    print("3. 텍스트 요청 테스트")
    print("=" * 60)
    
    try:
        form_data = {
            "text": "이 옷을 입혀줘",
            "session_id": "test_session_001"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/request",
            data=form_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 텍스트 요청 성공")
            print(f"   상태: {result.get('status')}")
            print(f"   메시지: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ 텍스트 요청 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_image_request():
    """이미지 요청 테스트"""
    print("\n" + "=" * 60)
    print("4. 이미지 요청 테스트")
    print("=" * 60)
    
    # 테스트 이미지 찾기 (uploads 또는 image 폴더)
    test_image_paths = [
        project_root / "uploads",
        project_root / "image",
    ]
    test_image = None
    for dir_path in test_image_paths:
        if dir_path.is_dir():
            for ext in ("*.png", "*.jpg", "*.jpeg"):
                for path in dir_path.glob(ext):
                    test_image = path
                    break
            if test_image:
                break
    
    if not test_image:
        print("⚠️  테스트 이미지를 찾을 수 없습니다.")
        print("   이미지 경로를 확인하거나 다른 이미지를 사용하세요.")
        return False
    
    try:
        with open(test_image, 'rb') as f:
            files = {
                "image": (test_image.name, f, "image/png")
            }
            data = {
                "text": "이 옷을 입혀줘",
                "session_id": "test_session_002"
            }
            
            print(f"   테스트 이미지: {test_image}")
            response = requests.post(
                "http://localhost:8000/api/v1/request",
                files=files,
                data=data,
                timeout=120  # 이미지 처리에는 시간이 걸릴 수 있음
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 이미지 요청 성공")
            print(f"   상태: {result.get('status')}")
            print(f"   메시지: {result.get('message', 'N/A')}")
            
            # 결과 데이터 확인
            data = result.get('data', {})
            if data:
                print(f"   결과 데이터 키: {list(data.keys())}")
            
            return True
        else:
            print(f"❌ 이미지 요청 실패: {response.status_code}")
            print(f"   응답: {response.text[:500]}")  # 처음 500자만
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("Fashion Agentic AI System - API 서버 테스트")
    print("=" * 60 + "\n")
    
    results = {
        "헬스체크": test_api_health(),
        "루트 엔드포인트": test_api_root(),
        "텍스트 요청": test_text_request(),
        "이미지 요청": test_image_request(),
    }
    
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print("\n⚠️  일부 테스트 실패")
        print("\n문제 해결:")
        print("1. API 서버가 실행 중인지 확인")
        print("2. 포트 8000이 사용 가능한지 확인")
        print("3. 오류 메시지를 확인하고 수정")
        return 1

if __name__ == "__main__":
    sys.exit(main())

