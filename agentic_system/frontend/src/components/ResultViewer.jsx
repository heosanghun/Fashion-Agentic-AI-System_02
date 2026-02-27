import { useState } from 'react';
import './ResultViewer.css';
import ModelViewer from './ModelViewer';

function ResultViewer({ result, image, personImage }) {
  const [thoughtsExpanded, setThoughtsExpanded] = useState(false);
  if (!result) {
    return (
      <div className="result-viewer">
        <div className="result-placeholder">
          <p>가상 피팅 결과가 여기에 나타납니다</p>
          <p className="hint">의류 이미지를 올리거나 설명을 입력한 뒤 요청 전송을 눌러보세요.</p>
        </div>
      </div>
    );
  }

  const status = result.status || 'unknown';
  const message = result.message || '';
  const data = result.data || {};
  const steps = result.steps || {};
  const finalResult = result.final_result || {};
  const planId = result.plan_id || '';
  const thoughts = result.thoughts || {};

  // 최종 결과에서 렌더링 이미지 경로 추출 (Try-On 결과 image_path 포함)
  const renderImagePath = finalResult?.result?.visualization?.image_path ||
                          finalResult?.result?.render_path ||
                          finalResult?.result?.image_path ||
                          data.visualization?.image_path ||
                          data.render_path;

  // 최종 결과에서 메시지 추출
  const finalMessage = finalResult?.result?.message || message;

  // 단계별 결과 추출
  const step1Result = steps['1']?.result || {};
  const step2Result = steps['2']?.result || {};
  const step3Result = steps['3']?.result || {};
  const step4Result = steps['4']?.result || {};

  return (
    <div className="result-viewer">
      <h2>가상 피팅 결과</h2>
      
      <div className="result-status">
        <span className={`status-badge status-${status}`}>
          {status === 'completed' ? '완료' : status === 'success' ? '성공' : status === 'error' ? '오류' : status === 'failed' ? '실패' : status}
        </span>
        {planId && <span className="plan-id">Plan ID: {planId}</span>}
      </div>

      {/* 2 판단 — 생각 및 판단 영역 (Gemini Thoughts 스타일) */}
      {(thoughts.intent || thoughts.abstract_plan || thoughts.execution_plan) && (
        <div className="thoughts-panel">
          <div className="thoughts-header">
            <span className="thoughts-icon" aria-hidden="true">◆</span>
            <strong className="thoughts-title">생각 및 판단</strong>
          </div>
          <button
            type="button"
            className={`thoughts-toggle ${thoughtsExpanded ? 'is-expanded' : ''}`}
            onClick={() => setThoughtsExpanded((e) => !e)}
            aria-expanded={thoughtsExpanded}
          >
            <span>{thoughtsExpanded ? '접기' : '펼쳐서 모델의 생각·판단 과정 보기'}</span>
            <span className="thoughts-chevron" aria-hidden="true">▼</span>
          </button>
          {thoughtsExpanded && (
            <div className="thoughts-content">
              {thoughts.intent && (
                <section className="thoughts-block">
                  <h4>① 의도 인식</h4>
                  <p><strong>유형:</strong> {thoughts.intent.label || thoughts.intent.type}</p>
                  {thoughts.intent.text_preview && <p><strong>입력 요약:</strong> {thoughts.intent.text_preview}</p>}
                  {thoughts.intent.has_image && <p>이미지 포함</p>}
                  {thoughts.intent.reason && <p className="thoughts-reason">{thoughts.intent.reason}</p>}
                </section>
              )}
              {thoughts.abstract_plan && (
                <section className="thoughts-block">
                  <h4>② 추상 계획 (Agent 1)</h4>
                  <p><strong>목표:</strong> {thoughts.abstract_plan.goal}</p>
                  <p><strong>유형:</strong> {thoughts.abstract_plan.plan_type}</p>
                  {thoughts.abstract_plan.steps?.length > 0 && (
                    <ul>
                      {thoughts.abstract_plan.steps.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  )}
                </section>
              )}
              {thoughts.execution_plan && (
                <section className="thoughts-block">
                  <h4>③ 실행 계획 (Agent 2)</h4>
                  {thoughts.execution_plan.plan_id && <p><strong>Plan ID:</strong> {thoughts.execution_plan.plan_id}</p>}
                  {thoughts.execution_plan.steps?.length > 0 && (
                    <ul className="thoughts-steps">
                      {thoughts.execution_plan.steps.map((step, i) => (
                        <li key={i}>
                          <strong>{step.step_id}</strong> → {step.tool}.{step.action}
                          {step.parameters && Object.keys(step.parameters).length > 0 && (
                            <pre className="thoughts-params">{JSON.stringify(step.parameters, null, 2)}</pre>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              )}
            </div>
          )}
        </div>
      )}

      {finalMessage && (
        <div className="result-message">
          <p>{finalMessage}</p>
        </div>
      )}

      {/* 최종 렌더링 이미지 표시 */}
      {renderImagePath && (
        <div className="render-section">
          <h3>최종 렌더링 결과</h3>
          {(finalMessage && (finalMessage.includes('의류 이미지를 표시') || finalMessage.includes('합성 이미지 생성이 지원되지 않'))) && (
            <p className="render-section-notice">합성 이미지가 생성되지 않아 업로드한 의류를 표시합니다. 의류 + 인물 두 장을 올리면 가상 피팅 합성이 시도됩니다.</p>
          )}
          <div className="render-container">
            <img 
              src={`http://localhost:8000/api/v1/file?path=${encodeURIComponent(renderImagePath)}`}
              alt="렌더링 결과"
              className="render-image"
              onError={(e) => {
                console.error('이미지 로드 실패:', renderImagePath);
                e.target.style.display = 'none';
                e.target.parentElement.innerHTML += '<p style="color: #ff6b6b;">이미지를 불러올 수 없습니다.</p>';
              }}
            />
          </div>
        </div>
      )}

      {/* 단계별 처리 결과 */}
      {Object.keys(steps).length > 0 && (
        <div className="steps-info">
          <h3>처리 단계</h3>
          <ul>
            {Object.entries(steps).map(([stepId, stepData]) => {
              const stepStatus = stepData.status || 'unknown';
              const stepResult = stepData.result || {};
              const stepMessage = stepResult.message || '';

              let stepDescription = '';
              if (stepId === '1') stepDescription = '1단계: 가상 피팅';
              else if (stepId === '2') stepDescription = '2단계: 패턴 생성';
              else if (stepId === '3') stepDescription = '3단계: 3D 변환';
              else if (stepId === '4') stepDescription = '4단계: 렌더링';
              else stepDescription = `${stepId}단계`;

              return (
                <li key={stepId}>
                  <strong>{stepDescription}</strong>
                  <span className={`step-status step-${stepStatus}`}>
                    {stepStatus === 'success' ? '✓ 완료' : stepStatus === 'error' ? '✗ 오류' : stepStatus}
                  </span>
                  {stepMessage && <div className="step-message">{stepMessage}</div>}
                  {stepResult.analysis && (
                    <div className="step-details">
                      <p>분석 결과:</p>
                      <pre>{JSON.stringify(stepResult.analysis, null, 2)}</pre>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* 이미지 분석 결과 */}
      {step1Result.analysis && (
        <div className="model-section">
          <h3>이미지 분석 결과</h3>
          <div className="analysis-result">
            <p><strong>의류 유형:</strong> {step1Result.analysis.garment_type}</p>
            <p><strong>스타일:</strong> {step1Result.analysis.style}</p>
            <p><strong>색상:</strong> {step1Result.analysis.color}</p>
            <p><strong>타입:</strong> {step1Result.analysis.type}</p>
          </div>
        </div>
      )}

      {/* 3D 메시 정보 */}
      {step3Result.mesh_info && (
        <div className="model-section">
          <h3>3D 메시 정보</h3>
          <div className="mesh-info">
            <p><strong>정점 수:</strong> {step3Result.mesh_info.vertices?.toLocaleString()}</p>
            <p><strong>면 수:</strong> {step3Result.mesh_info.faces?.toLocaleString()}</p>
            <p><strong>포맷:</strong> {step3Result.mesh_info.format}</p>
            {step3Result.mesh_path && (
              <p><strong>파일 경로:</strong> {step3Result.mesh_path}</p>
            )}
          </div>
        </div>
      )}

      {/* 기존 상품 추천 결과 */}
      {data.recommendations && (
        <div className="result-section">
          <h4>추천 상품</h4>
          <div className="products-grid">
            {data.recommendations.map((product, index) => (
              <div key={index} className="product-card">
                <h5>{product.name}</h5>
                <p>카테고리: {product.category}</p>
                <p>스타일: {product.style}</p>
                <p>색상: {product.color}</p>
                <p>가격: {product.price?.toLocaleString()}원</p>
                <p>브랜드: {product.brand}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3D 시각화 (기존 방식 지원) */}
      {data.visualization && !renderImagePath && (
        <div className="result-section">
          <h4>3D 시각화</h4>
          <div className="visualization-container">
            {data.visualization.mesh_path && (
              <ModelViewer meshPath={data.visualization.mesh_path} />
            )}
            {data.visualization.message && (
              <p>{data.visualization.message}</p>
            )}
          </div>
        </div>
      )}

      {/* 오류 표시 */}
      {(status === 'error' || status === 'failed') && (
        <div className="result-error">
          <p>오류가 발생했습니다.</p>
          {data.error && (
            <pre>{typeof data.error === 'string' ? data.error : JSON.stringify(data.error, null, 2)}</pre>
          )}
        </div>
      )}

      {/* 전체 결과 데이터 (디버깅용) */}
      <div className="result-section">
        <h4>전체 결과 데이터</h4>
        <details>
          <summary>데이터 보기</summary>
          <pre className="full-data">{JSON.stringify(result, null, 2)}</pre>
        </details>
      </div>

      {/* 원본 이미지 표시 (있는 경우) */}
      {image && (
        <div className="result-section">
          <h4>업로드된 이미지</h4>
          <div className="uploaded-image">
            <img
              src={URL.createObjectURL(image)}
              alt="업로드된 이미지"
              style={{ maxWidth: '400px', maxHeight: '400px' }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultViewer;
