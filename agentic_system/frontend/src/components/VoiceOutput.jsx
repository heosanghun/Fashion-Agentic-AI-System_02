import { useState, useCallback, useEffect } from 'react';
import './VoiceOutput.css';

function VoiceOutput({ text, disabled }) {
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => () => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }, []);

  const speak = useCallback(() => {
    if (!text || typeof window === 'undefined' || !window.speechSynthesis) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'ko-KR';
    u.rate = 1;
    u.onend = () => setSpeaking(false);
    u.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(u);
    setSpeaking(true);
  }, [text, speaking]);

  const hasTTS = typeof window !== 'undefined' && window.speechSynthesis;
  if (!hasTTS || !text) return null;

  return (
    <button
      type="button"
      className={`voice-btn voice-speaker ${speaking ? 'speaking' : ''}`}
      onClick={speak}
      disabled={disabled}
      title={speaking ? '읽기 중지' : '음성으로 들기'}
      aria-label={speaking ? '읽기 중지' : '음성 재생'}
    >
      <span className="voice-icon" aria-hidden="true">
        {speaking ? '⏹' : '🔊'}
      </span>
      <span className="voice-label">{speaking ? '중지' : '들기'}</span>
    </button>
  );
}

export default VoiceOutput;
