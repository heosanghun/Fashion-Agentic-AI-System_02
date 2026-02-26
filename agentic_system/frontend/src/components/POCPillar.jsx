/**
 * POC 안내 — 패션 Agentic AI 가상 피팅 POC 개발 계획서 뼈대
 * 인식-판단-행동, Agent 1·2, 종합 시스템 구성도, 21가지 디자인 패턴 & POC 요약
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import './POCPillar.css';

const SYSTEM_DIAGRAM_URL = '/system-diagram.jpg';
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.25;

export default function POCPillar({ activeSteps = [1] }) {
  const [open, setOpen] = useState(true);
  const [diagramOpen, setDiagramOpen] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0, tx: 0, ty: 0 });

  const isActive = (step) => Array.isArray(activeSteps) && activeSteps.includes(step);

  const openDiagram = useCallback(() => {
    setDiagramOpen(true);
    setScale(1);
    setTranslate({ x: 0, y: 0 });
  }, []);

  const zoomIn = useCallback(() => setScale((s) => Math.min(MAX_ZOOM, s + ZOOM_STEP)), []);
  const zoomOut = useCallback(() => setScale((s) => Math.max(MIN_ZOOM, s - ZOOM_STEP)), []);
  const resetView = useCallback(() => {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
  }, []);

  const handleMouseDown = useCallback((e) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY, tx: translate.x, ty: translate.y };
  }, [translate.x, translate.y]);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    setTranslate({
      x: dragStart.current.tx + (e.clientX - dragStart.current.x),
      y: dragStart.current.ty + (e.clientY - dragStart.current.y),
    });
  }, [isDragging]);

  const handleMouseUp = useCallback(() => setIsDragging(false), []);
  const handleMouseLeave = useCallback(() => setIsDragging(false), []);

  const viewportRef = useRef(null);
  useEffect(() => {
    if (!diagramOpen || !viewportRef.current) return;
    const el = viewportRef.current;
    const onWheel = (e) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
      setScale((s) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, s + delta)));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [diagramOpen]);

  return (
    <>
      <aside className={`poc-pillar ${open ? 'is-open' : ''}`} role="complementary" aria-label="POC 안내">
        <button
          type="button"
          className="poc-pillar-toggle"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-label={open ? '안내 접기' : '안내 펼치기'}
        >
          <span className="poc-pillar-toggle-icon">{open ? '◀' : '▶'}</span>
          <span className="poc-pillar-toggle-text">POC 안내</span>
        </button>

        <div className="poc-pillar-content">
          <div className="poc-pillar-title">
            <span className="poc-pillar-doc">개발 계획서 v3.0</span>
            <span className="poc-pillar-flow">인식 → 판단 → 행동</span>
          </div>

          <ol className="poc-pillar-steps">
            <li className={`poc-pillar-step ${isActive(1) ? 'is-active' : ''}`}>
              <span className="poc-pillar-step-num">1</span>
              <strong>인식 (Perception)</strong>
              <p>Custom UI로 텍스트·이미지 입력 → 사용자 의도 인지</p>
            </li>
            <li className={`poc-pillar-step ${isActive(2) ? 'is-active' : ''}`}>
              <span className="poc-pillar-step-num">2</span>
              <strong>판단 (Judgment)</strong>
              <p>
                <em>오케스트레이션</em> Agent Runtime(Agent 1): 전략·계획 수립<br />
                <em>F.LLM</em> Agent 2: 실행 계획(JSON) 생성
              </p>
            </li>
            <li className={`poc-pillar-step ${isActive(3) ? 'is-active' : ''}`}>
              <span className="poc-pillar-step-num">3</span>
              <strong>행동 (Action)</strong>
              <p>Extensions(Tools) 순차 호출 → 결과 시각화</p>
            </li>
          </ol>

          <div className="poc-pillar-core">
            <div className="poc-pillar-core-item">
              <span className="poc-pillar-core-label">오케스트레이션</span>
              <span className="poc-pillar-core-name">Agent Runtime (Agent 1)</span>
            </div>
            <div className="poc-pillar-core-item">
              <span className="poc-pillar-core-label">작업 계획 생성</span>
              <span className="poc-pillar-core-name">F.LLM (Agent 2)</span>
            </div>
          </div>

          <p className="poc-pillar-note">
            이 뼈대는 계획서의 핵심이며, 모든 기능은 이 3단계와 Agent 1·2를 기반으로 동작합니다.
          </p>

          <button
            type="button"
            className="poc-pillar-diagram-btn"
            onClick={openDiagram}
            aria-label="종합 시스템 구성도 보기"
          >
            종합 시스템 구성도
          </button>

          <button
            type="button"
            className="poc-pillar-guide-btn"
            onClick={() => setGuideOpen(true)}
            aria-label="21가지 패턴과 POC 요약 보기"
          >
            21가지 패턴 & POC 요약
          </button>
        </div>
      </aside>

      {guideOpen && (
        <div
          className="poc-pillar-guide-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="21가지 디자인 패턴 및 POC 요약"
          onClick={() => setGuideOpen(false)}
        >
          <div className="poc-pillar-guide-panel" onClick={(e) => e.stopPropagation()}>
            <div className="poc-pillar-guide-header">
              <h2>21가지 디자인 패턴 & POC 요약</h2>
              <button type="button" className="poc-pillar-guide-close" onClick={() => setGuideOpen(false)} aria-label="닫기">×</button>
            </div>
            <div className="poc-pillar-guide-body">
              <section className="poc-guide-section">
                <h3>현재 POC에서 적용한 5가지 패턴 (코드 구현 완료)</h3>
                <p className="poc-guide-lead">Google 등에서 제시하는 21개 Agent Design Patterns 중, PoC 단계에서는 아래 5가지만 적용해 구현했습니다.</p>
                <div className="poc-guide-table-wrap">
                  <table className="poc-guide-table">
                    <thead>
                      <tr><th>번호</th><th>패턴명</th><th>의미</th><th>이 프로젝트에서의 구현</th></tr>
                    </thead>
                    <tbody>
                      <tr><td>1</td><td>프롬프트 체이닝</td><td>복잡한 작업을 여러 단계로 나누어 순차 처리</td><td>추상 계획 → 실행 계획(JSON) → 단계별 도구 순차 실행</td></tr>
                      <tr><td>2</td><td>라우팅</td><td>사용자 입력에 따라 다음 경로를 동적으로 결정</td><td>의도 분석(3D 생성 / 의류 추천 / 대화 / 정보 검색) 후 해당 플로우로 분기</td></tr>
                      <tr><td>3</td><td>도구 사용</td><td>외부 API·함수를 호출해 실제 작업 수행</td><td>Agent Runtime이 등록된 도구(gemini_tryon, 상품 검색 등)를 순차 호출</td></tr>
                      <tr><td>4</td><td>반성</td><td>결과를 스스로 검증·평가</td><td>실행 결과를 _evaluate_result로 검사해 성공/실패 판단</td></tr>
                      <tr><td>5</td><td>복구</td><td>오류 시 재시도 등으로 시스템이 멈추지 않도록 대처</td><td>실패 시 최대 1회 _execute_plan 재실행(자기 수정 루프)</td></tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="poc-guide-section">
                <h3>나머지 16개 패턴 (Pilot 단계 적용 예정)</h3>
                <p className="poc-guide-lead">아래 패턴들은 문서에 정의되어 있으며, Pilot 1·2 단계에서 점진적으로 도입 예정입니다.</p>
                <ul className="poc-guide-list">
                  <li><strong>6.</strong> 병렬화 — 여러 작업 동시 실행</li>
                  <li><strong>7.</strong> 계획 — 사용자 프롬프트 분석 후 최적 작업 계획 수립</li>
                  <li><strong>8.</strong> 다중 에이전트 협업 — 전문성별 에이전트 협력</li>
                  <li><strong>9.</strong> 메모리 관리 — 대화·선호도 기억, 개인화</li>
                  <li><strong>10.</strong> 지식 검색(RAG) — 외부 DB 검색으로 판단 정확도 향상</li>
                  <li><strong>11.</strong> 가드레일/안전 — 부적절 요청 차단</li>
                  <li><strong>12.</strong> 평가 및 모니터링 — 성능 측정·추적</li>
                  <li><strong>13.</strong> 자원 인식 최적화 — 비용·자원 동적 선택</li>
                  <li><strong>14.</strong> 인간 참여 루프 — 불확실 시 사람 개입 요청</li>
                  <li><strong>15.</strong> 에이전트 간 통신(A2A) — 표준 프로토콜로 데이터 교환</li>
                  <li><strong>16.</strong> 목표 설정 및 모니터링 — 장기 목표·제약 추적</li>
                  <li><strong>17.</strong> 우선순위 지정 — 요청 중요도별 처리 순서</li>
                  <li><strong>18.</strong> 추론 기법(CoT 등) — 논리적 사고로 복잡 질문 대응</li>
                  <li><strong>19.</strong> 학습과 적응 — 피드백으로 성능 개선</li>
                  <li><strong>20.</strong> 탐험과 발견 — 신규 지식·트렌드 탐색</li>
                  <li><strong>21.</strong> 모델 컨텍스트 프로토콜(MCP) — 표준 인터페이스로 외부 도구 연동</li>
                </ul>
              </section>

              <section className="poc-guide-section">
                <h3>21가지 패턴 한눈에</h3>
                <div className="poc-guide-table-wrap">
                  <table className="poc-guide-table poc-guide-table-compact">
                    <thead>
                      <tr><th>구분</th><th>패턴 수</th><th>내용</th></tr>
                    </thead>
                    <tbody>
                      <tr><td>현재 POC 적용</td><td>5개</td><td>프롬프트 체이닝, 라우팅, 도구 사용, 반성, 복구</td></tr>
                      <tr><td>Pilot 적용 예정</td><td>16개</td><td>병렬화, 계획, 다중 에이전트 협업, RAG, 메모리, 가드레일, A2A, MCP 등</td></tr>
                      <tr><td>합계</td><td>21개</td><td>Google 등에서 검증된 Agent Design Patterns 기반</td></tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="poc-guide-section">
                <h3>ADK(Agent Development Kit) 관련</h3>
                <div className="poc-guide-table-wrap">
                  <table className="poc-guide-table">
                    <thead>
                      <tr><th>항목</th><th>내용</th></tr>
                    </thead>
                    <tbody>
                      <tr><td>ADK 사용 여부</td><td><strong>미사용</strong> — Google ADK(Agent Development Kit)를 사용하지 않음</td></tr>
                      <tr><td>현재 구현 방식</td><td><strong>자체 구현</strong> — Agent Runtime(Agent 1), F.LLM(Agent 2)을 코드로 직접 구현</td></tr>
                      <tr><td>참고</td><td>설계는 21가지 디자인 패턴 사상을 참고했으며, 프레임워크는 LangChain/LlamaIndex 대신 자체 오케스트레이션으로 동작</td></tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="poc-guide-section">
                <h3>코드·디렉토리 구조 요약</h3>
                <p className="poc-guide-lead">핵심 코드 위치와 기능·작동 원리를 한눈에 볼 수 있습니다. 상세는 doc/코드_및_디렉토리_구조_가이드.md 참고.</p>
                <div className="poc-guide-table-wrap">
                  <table className="poc-guide-table">
                    <thead>
                      <tr><th>경로</th><th>기능</th><th>작동 원리</th></tr>
                    </thead>
                    <tbody>
                      <tr><td>api/main.py</td><td>FastAPI 서버, 요청 진입점</td><td>Payload 생성 → AgentRuntime.process_request → JSON 응답</td></tr>
                      <tr><td>core/agent_runtime.py</td><td>Agent 1 오케스트레이션</td><td>의도 분석 → 추상계획 → RAG → 실행계획 → 도구 순차 실행 → 자기수정 루프</td></tr>
                      <tr><td>core/f_llm.py</td><td>Agent 2 실행 계획 생성</td><td>plan_type별 steps(JSON) 생성, RAG로 계획 보강</td></tr>
                      <tr><td>core/memory.py</td><td>세션 메모리</td><td>ShortTermMemory로 대화 기록·컨텍스트 저장</td></tr>
                      <tr><td>tools/gemini_tryon.py</td><td>가상 피팅 도구</td><td>Gemini API로 의류 분석·Try-On 이미지 생성</td></tr>
                      <tr><td>data_stores/rag.py</td><td>RAG 통합</td><td>로컬+외부+Mock 검색 결과를 rag_suggestions로 통합</td></tr>
                      <tr><td>frontend/App.jsx</td><td>프론트 앱·상태</td><td>입력 → /api/v1/request → messages/result 반영, 채팅·결과 뷰</td></tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          </div>
        </div>
      )}

      {diagramOpen && (
        <div
          className="poc-pillar-diagram-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="종합 시스템 구성도"
          onClick={() => setDiagramOpen(false)}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
        >
          <div className="poc-pillar-diagram-wrap" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="poc-pillar-diagram-close"
              onClick={() => setDiagramOpen(false)}
              aria-label="닫기"
            >
              ×
            </button>
            <div className="poc-pillar-diagram-zoom-bar">
              <button type="button" onClick={zoomIn} aria-label="확대">+</button>
              <span className="poc-pillar-diagram-zoom-value">{Math.round(scale * 100)}%</span>
              <button type="button" onClick={zoomOut} aria-label="축소">−</button>
              <button type="button" onClick={resetView} aria-label="초기화">초기화</button>
            </div>
            <div
              ref={viewportRef}
              className="poc-pillar-diagram-viewport"
              onMouseDown={handleMouseDown}
              style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
            >
              <div
                className="poc-pillar-diagram-transform"
                style={{
                  transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`,
                }}
              >
                <img
                  src={SYSTEM_DIAGRAM_URL}
                  alt="Fashion Agentic AI System 종합 시스템 구성도"
                  className="poc-pillar-diagram-img"
                  draggable={false}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
