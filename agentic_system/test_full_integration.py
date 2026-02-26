#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전체 시스템 통합 테스트

프론트엔드와 백엔드가 실제로 작동하는지 테스트
"""

import sys
import os
import time
import requests
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_api_server():
    """API 서버 연결 테스트"""
    print("=" * 60)
    print("1. API 서버 연결 테스트")
    print("=" * 60)
    
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ API 서버 정상 작동")
                return True
        except:
            if i < max_retries - 1:
                print(f"⏳ 서버 시작 대기 중... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print("❌ API 서버 연결 실패")
                print("   서버를 시작해주세요: python agentic_system/start_api_server.py")
                return False
    
    return False

def test_frontend_server():
    """프론트엔드 서버 연결 테스트"""
    print("\n" + "=" * 60)
    print("2. 프론트엔드 서버 연결 테스트")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:3000", timeout=2)
        if response.status_code == 200:
            print("✅ 프론트엔드 서버 정상 작동")
            return True
    except:
        print("⚠️  프론트엔드 서버가 실행되지 않았습니다.")
        print("   프론트엔드를 시작해주세요:")
        print("   cd agentic_system/frontend && npm install && npm run dev")
        return False
    
    return False

def test_text_request():
    """텍스트 요청 테스트"""
    print("\n" + "=" * 60)
    print("3. 텍스트 요청 처리 테스트")
    print("=" * 60)
    
    try:
        form_data = {
            "text": "빨간색 원피스를 추천해줘",
            "session_id": "test_integration_001"
        }
        
        print("   요청 전송 중...")
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
            
            # 결과 데이터 확인
            data = result.get('data', {})
            if data:
                print(f"   결과 데이터 키: {list(data.keys())[:5]}...")
            
            return True
        else:
            print(f"❌ 텍스트 요청 실패: {response.status_code}")
            print(f"   응답: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_image_request():
    """이미지 요청 테스트"""
    print("\n" + "=" * 60)
    print("4. 이미지 요청 처리 테스트")
    print("=" * 60)
    
    # 테스트 이미지 찾기 (uploads 또는 image 폴더)
    test_image_dirs = [project_root / "uploads", project_root / "image"]
    test_image = None
    for dir_path in test_image_dirs:
        if dir_path.is_dir():
            for ext in ("*.png", "*.jpg", "*.jpeg"):
                for path in dir_path.glob(ext):
                    test_image = path
                    break
            if test_image:
                break
    
    if not test_image:
        print("⚠️  테스트 이미지를 찾을 수 없습니다.")
        return False
    
    try:
        with open(test_image, 'rb') as f:
            files = {
                "image": (test_image.name, f, "image/png")
            }
            data = {
                "text": "이 옷을 입혀줘",
                "session_id": "test_integration_002"
            }
            
            print(f"   이미지: {test_image.name}")
            print("   요청 전송 중...")
            
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
                print(f"   결과 데이터 키: {list(data.keys())[:5]}...")
            
            return True
        else:
            print(f"❌ 이미지 요청 실패: {response.status_code}")
            print(f"   응답: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """에러 처리 테스트"""
    print("\n" + "=" * 60)
    print("5. 에러 처리 테스트")
    print("=" * 60)
    
    # 빈 요청 테스트
    try:
        form_data = {}
        response = requests.post(
            "http://localhost:8000/api/v1/request",
            data=form_data,
            timeout=10
        )
        
        # 에러가 적절히 처리되는지 확인
        if response.status_code in [200, 400, 422]:
            print("✅ 에러 처리 정상")
            if response.status_code != 200:
                print(f"   예상된 에러 응답: {response.status_code}")
            return True
        else:
            print(f"⚠️  예상치 못한 상태 코드: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("Fashion Agentic AI System - 전체 통합 테스트")
    print("=" * 60 + "\n")
    
    results = {
        "API 서버": test_api_server(),
        "프론트엔드 서버": test_frontend_server(),
        "텍스트 요청": test_text_request(),
        "이미지 요청": test_image_request(),
        "에러 처리": test_error_handling(),
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
        print("\n시스템이 정상적으로 작동하고 있습니다.")
        return 0
    else:
        print("\n⚠️  일부 테스트 실패")
        print("\n문제 해결:")
        print("1. API 서버 시작: python agentic_system/start_api_server.py")
        print("2. 프론트엔드 의존성 설치: cd agentic_system/frontend && npm install")
        print("3. 프론트엔드 시작: cd agentic_system/frontend && npm run dev")
        return 1

if __name__ == "__main__":
    sys.exit(main())

