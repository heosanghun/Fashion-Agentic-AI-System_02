#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGarment 실행 분석 스크립트
실제로 ChatGarment가 동작했는지, Mock 모드로 동작했는지 확인
"""

import sys
import os
from pathlib import Path
import json

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agentic_system"))

def analyze_chatgarment_status():
    """ChatGarment 상태 분석"""
    print("=" * 80)
    print("ChatGarment 실행 상태 심층 분석")
    print("=" * 80)
    
    # 1. 모델 파일 확인
    print("\n[1] 모델 파일 확인")
    print("-" * 80)
    
    checkpoint_path = project_root / "checkpoints" / "try_7b_lr1e_4_v3_garmentcontrol_4h100_v4_final" / "pytorch_model.bin"
    model_path = project_root / "checkpoints" / "llava-v1.5-7b"
    
    print(f"체크포인트 경로: {checkpoint_path}")
    print(f"  존재 여부: {'✅ 존재' if checkpoint_path.exists() else '❌ 없음'}")
    if checkpoint_path.exists():
        size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
        print(f"  파일 크기: {size_mb:.2f} MB")
    
    print(f"\n기본 모델 경로: {model_path}")
    print(f"  존재 여부: {'✅ 존재' if model_path.exists() else '❌ 없음'}")
    
    # 2. ChatGarment 모듈 임포트 확인
    print("\n[2] ChatGarment 모듈 임포트 확인")
    print("-" * 80)
    
    try:
        from agentic_system.tools.chatgarment_integration import ChatGarmentPipeline, CHATGARMENT_AVAILABLE
        print(f"CHATGARMENT_AVAILABLE: {CHATGARMENT_AVAILABLE}")
        print(f"ChatGarmentPipeline 클래스: {'✅ 임포트 성공' if ChatGarmentPipeline else '❌ 임포트 실패'}")
    except Exception as e:
        print(f"❌ 모듈 임포트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Extensions2DTo3D 초기화 확인
    print("\n[3] Extensions2DTo3D 초기화 확인")
    print("-" * 80)
    
    try:
        from agentic_system.tools.extensions import Extensions2DTo3D
        tool = Extensions2DTo3D()
        print(f"모델 로드 상태: {tool.model_loaded}")
        print(f"ChatGarment 파이프라인: {'✅ 초기화됨' if tool.chatgarment_pipeline else '❌ 초기화 안됨'}")
        if tool.chatgarment_pipeline:
            print(f"  파이프라인 모델 로드 상태: {tool.chatgarment_pipeline.model_loaded if hasattr(tool.chatgarment_pipeline, 'model_loaded') else 'N/A'}")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 실제 모델 로딩 시도
    print("\n[4] 실제 모델 로딩 시도")
    print("-" * 80)
    
    try:
        from agentic_system.tools.extensions import Extensions2DTo3D
        tool = Extensions2DTo3D()
        print("모델 로딩 시도 중...")
        tool._load_model()
        print(f"모델 로드 결과: {tool.model_loaded}")
        if tool.model_loaded:
            print("✅ 실제 ChatGarment 모델이 로드되었습니다!")
        else:
            print("❌ 모델 로드 실패 - Mock 모드로 동작합니다")
    except Exception as e:
        print(f"❌ 모델 로딩 오류: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 출력 파일 분석
    print("\n[5] 출력 파일 분석")
    print("-" * 80)
    
    pattern_file = project_root / "outputs" / "patterns" / "pattern.json"
    mesh_file = project_root / "outputs" / "3d_models" / "garment.obj"
    
    if pattern_file.exists():
        print(f"✅ 패턴 파일 존재: {pattern_file}")
        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                pattern_data = json.load(f)
            print(f"  생성자: {pattern_data.get('created_by', 'N/A')}")
            if pattern_data.get('created_by') == 'mock_generator':
                print("  ⚠️ Mock 모드로 생성된 파일입니다!")
        except Exception as e:
            print(f"  파일 읽기 오류: {e}")
    else:
        print(f"❌ 패턴 파일 없음: {pattern_file}")
    
    if mesh_file.exists():
        print(f"\n✅ 3D 모델 파일 존재: {mesh_file}")
        try:
            with open(mesh_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if "Mock" in content or "mock" in content:
                print("  ⚠️ Mock 모드로 생성된 파일입니다!")
                print("  파일 내용 (처음 200자):")
                print(f"  {content[:200]}")
        except Exception as e:
            print(f"  파일 읽기 오류: {e}")
    else:
        print(f"❌ 3D 모델 파일 없음: {mesh_file}")
    
    # 6. 환경 변수 확인
    print("\n[6] 환경 변수 확인")
    print("-" * 80)
    
    use_service = os.getenv("USE_CHATGARMENT_SERVICE", "false")
    service_url = os.getenv("CHATGARMENT_SERVICE_URL", "http://localhost:9000")
    print(f"USE_CHATGARMENT_SERVICE: {use_service}")
    print(f"CHATGARMENT_SERVICE_URL: {service_url}")
    
    # 7. 의존성 확인
    print("\n[7] 의존성 확인")
    print("-" * 80)
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"  CUDA 사용 가능: {torch.cuda.is_available()}")
    except ImportError:
        print("❌ PyTorch 미설치")
    
    try:
        import transformers
        print(f"✅ Transformers: {transformers.__version__}")
    except ImportError:
        print("❌ Transformers 미설치")
    
    try:
        from PIL import Image
        print("✅ Pillow (PIL) 설치됨")
    except ImportError:
        print("❌ Pillow (PIL) 미설치")
    
    # 8. 최종 결론
    print("\n" + "=" * 80)
    print("최종 분석 결과")
    print("=" * 80)
    
    # 모델 파일 존재 여부
    model_exists = checkpoint_path.exists() and model_path.exists()
    # 모델 로드 상태
    try:
        from agentic_system.tools.extensions import Extensions2DTo3D
        tool = Extensions2DTo3D()
        tool._load_model()
        model_loaded = tool.model_loaded
    except:
        model_loaded = False
    
    # 출력 파일이 Mock인지 확인
    is_mock_output = False
    if pattern_file.exists():
        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                pattern_data = json.load(f)
            if pattern_data.get('created_by') == 'mock_generator':
                is_mock_output = True
        except:
            pass
    
    print(f"\n모델 파일 존재: {'✅' if model_exists else '❌'}")
    print(f"모델 로드 성공: {'✅' if model_loaded else '❌'}")
    print(f"출력이 Mock 모드: {'⚠️ 예' if is_mock_output else '✅ 아니오'}")
    
    if is_mock_output and not model_loaded:
        print("\n⚠️ 결론: ChatGarment 모델이 로드되지 않아 Mock 모드로 동작했습니다.")
        print("   실제 티셔츠 이미지가 분석되지 않았고, 큐브 형태의 Mock 3D 모델이 생성되었습니다.")
    elif is_mock_output and model_loaded:
        print("\n⚠️ 결론: 모델은 로드되었지만 Mock 모드로 동작했습니다.")
        print("   코드 로직에서 Mock 모드로 전환된 것으로 보입니다.")
    elif not is_mock_output:
        print("\n✅ 결론: 실제 ChatGarment 모델이 동작한 것으로 보입니다.")
    else:
        print("\n❓ 결론: 상태를 명확히 파악할 수 없습니다.")

if __name__ == "__main__":
    analyze_chatgarment_status()

