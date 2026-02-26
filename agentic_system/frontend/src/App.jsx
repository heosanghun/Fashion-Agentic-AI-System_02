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
  const [image, setImage] = useState(null);
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

  const handleSubmit = async () => {
    if (!text && !image) {
      setError('이미지 또는 텍스트 입력이 필요합니다.');
      return;
    }

    const userContent = text || '(이미지만 첨부)';
    const imageName = image ? image.name : null;
    setMessages((prev) => [...prev, { role: 'user', content: userContent, imageName }]);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      if (text) {
        formData.append('text', text);
      }
      if (image) {
        formData.append('image', image);
      }
      formData.append('session_id', sessionId);

      const response = await axios.post('http://localhost:8000/api/v1/request', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000,
      });

      const data = response.data;
      const assistantMessage = data.message || '응답이 없습니다.';
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: assistantMessage,
        openaiError: data.openai_error || null,
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
          onImageChange={handleImageChange}
          onSubmit={handleSubmit}
          loading={loading}
        />

        {result && (
          <>
            <div className="status-section">
              <StatusBar loading={loading} progress={result.status === 'success' || result.status === 'completed' ? '완료' : result.status === 'failed' ? '실패' : undefined} status={result.status} />
            </div>
            <div className={`result-section result-reveal`}>
              <ResultViewer result={result} image={image} />
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
