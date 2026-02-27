import { useState } from 'react';
import axios from 'axios';
import './App.css';
import StatusBar from './components/StatusBar';
import ResultViewer from './components/ResultViewer';
import ThemeToggle from './components/ThemeToggle';
import POCPillar from './components/POCPillar';
import SimplePromptBar from './components/SimplePromptBar';
import ChatArea from './components/ChatArea';

function App() {
  const [image, setImage] = useState(null);           // 입을 옷 사진 (의류)
  const [personImage, setPersonImage] = useState(null); // 내 사진 (인물)
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sessionId] = useState(`session_${Date.now()}`);

  const handleImageChange = (file) => {
    setImage(file ?? null);
    setError(null);
  };
  const handlePersonImageChange = (file) => {
    setPersonImage(file ?? null);
    setError(null);
  };

  const handleSubmit = async () => {
    if (!text && !image && !personImage) {
      setError('텍스트 또는 이미지(의류/인물) 중 하나는 필요합니다.');
      return;
    }

    const userContent = text || (image || personImage ? '(이미지 첨부)' : '');
    const imageName = image ? `옷: ${image.name}` : null;
    const personName = personImage ? `인물: ${personImage.name}` : null;
    setMessages((prev) => [...prev, { role: 'user', content: userContent, imageName: imageName || personName }]);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      if (text) formData.append('text', text);
      if (image) formData.append('image', image);           // 의류
      if (personImage) formData.append('person_image', personImage); // 인물
      formData.append('session_id', sessionId);

      // 의류+인물 둘 다 있으면 직통 Try-On API 사용 (POC 뼈대 경유 없음). 404면 기존 API로 재시도
      const useDirectTryon = image && personImage;
      const tryonPayload = useDirectTryon
        ? (() => { const fd = new FormData(); fd.append('image', image); fd.append('person_image', personImage); fd.append('session_id', sessionId); return fd; })()
        : null;
      const apiOpts = {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      };

      let response;
      if (useDirectTryon && tryonPayload) {
        try {
          response = await axios.post('http://localhost:8000/api/v1/tryon', tryonPayload, apiOpts);
        } catch (directErr) {
          if (directErr.response?.status === 404) {
            response = await axios.post('http://localhost:8000/api/v1/request', formData, apiOpts);
          } else {
            throw directErr;
          }
        }
      } else {
        response = await axios.post('http://localhost:8000/api/v1/request', formData, apiOpts);
      }

      const data = response.data;
      const assistantMessage = data.message || '응답이 없습니다.';
      // Try-On 결과가 있으면 대화(OpenAI) 오류는 표시하지 않음
      const showOpenAIError = data.chat_only && (data.openai_error || null);
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: assistantMessage,
        openaiError: showOpenAIError || null,
      }]);

      if (!data.chat_only) {
        setResult(data);
      }
    } catch (err) {
      console.error('요청 오류:', err);
      const errMsg = err.response
        ? `서버 오류: ${err.response.status} - ${err.response.data?.detail || err.response.data?.message || '알 수 없는 오류'}`
        : err.request
          ? '서버에 연결할 수 없습니다. API 서버가 실행 중인지 확인하세요.'
          : `오류 발생: ${err.message}`;
      setError(errMsg);
      setMessages((prev) => [...prev, { role: 'assistant', content: errMsg }]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setImage(null);
    setPersonImage(null);
    setText('');
    setResult(null);
    setError(null);
    setMessages([]);
  };

  /* POC 기둥: 채팅만 → 1, Try-On 실행 중 → 2, 결과 도착 → 1·2·3 */
  const activeSteps = result ? [1, 2, 3] : loading ? [1, 2] : [1];

  return (
    <div className="app">
      <POCPillar activeSteps={activeSteps} />
      <header className="app-header">
        <div className="app-header-actions">
          <ThemeToggle />
        </div>
        <span className="hero-badge">AI Virtual Fitting</span>
        <h1>가상으로 입어보는<br />나만의 스타일</h1>
        <p className="hero-tagline">옷을 주문하기 전에, AI가 먼저 입어보게 해드려요. 이미지만 올리면 끝.</p>
      </header>

      <div className="app-container">
        <ChatArea messages={messages} />

        <SimplePromptBar
          text={text}
          setText={setText}
          image={image}
          personImage={personImage}
          onImageChange={handleImageChange}
          onPersonImageChange={handlePersonImageChange}
          onSubmit={handleSubmit}
          loading={loading}
        />

        {result && (
          <>
            <div className="status-section">
              <StatusBar loading={loading} progress={result.status === 'success' || result.status === 'completed' ? '완료' : result.status === 'failed' ? '실패' : undefined} status={result.status} />
            </div>
            <div className={`result-section result-reveal`}>
              <ResultViewer result={result} image={image} personImage={personImage} />
            </div>
          </>
        )}

        {error && !result && (
          <div className="error-section">
            <h3>오류 발생</h3>
            <p>{error}</p>
          </div>
        )}
      </div>

      <footer className="app-footer">
        <div className="footer-branding">
          <div className="footer-logo">
            <img src="/simsreality-logo.png" alt="SIMSREALITY" className="logo-image" onError={(e) => e.target.style.display = 'none'} />
          </div>
          <div className="footer-divider"></div>
          <p className="footer-text">Fashion Agentic AI · Virtual Fitting</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
