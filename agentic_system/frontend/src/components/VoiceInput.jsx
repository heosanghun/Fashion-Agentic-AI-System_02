import { useState, useRef, useCallback } from 'react';
import './VoiceInput.css';

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function VoiceInput({ onTranscript, disabled, compact }) {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState(null);
  const recognitionRef = useRef(null);

  const startRecording = useCallback(() => {
    if (!SpeechRecognition) {
      setError('이 브라우저는 음성 인식을 지원하지 않습니다. Chrome을 사용해 주세요.');
      return;
    }
    setError(null);
    const recognition = new SpeechRecognition();
    recognition.lang = 'ko-KR';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let finalText = '';
      let interimText = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalText += transcript;
        } else {
          interimText += transcript;
        }
      }
      if (finalText && onTranscript) {
        onTranscript((prev) => (prev ? prev + finalText : finalText));
      }
    };

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        setError('마이크 권한을 허용해 주세요.');
      } else {
        setError(event.error);
      }
      setRecording(false);
    };

    recognition.onend = () => {
      setRecording(false);
    };

    try {
      recognition.start();
      recognitionRef.current = recognition;
      setRecording(true);
    } catch (e) {
      setError(e.message || '음성 인식을 시작할 수 없습니다.');
    }
  }, [onTranscript]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setRecording(false);
  }, []);

  const toggle = () => {
    if (recording) stopRecording();
    else startRecording();
  };

  return (
    <div className="voice-input-wrap">
      <button
        type="button"
        className={`voice-btn voice-mic ${recording ? 'recording' : ''}`}
        onClick={toggle}
        disabled={disabled}
        title={recording ? '녹음 중지' : '음성으로 입력'}
        aria-label={recording ? '녹음 중지' : '음성 입력'}
      >
        <span className="voice-icon" aria-hidden="true">
          {recording ? '⏹' : '🎤'}
        </span>
        {!compact && <span className="voice-label">{recording ? '중지' : '음성'}</span>}
      </button>
      {error && !compact && <span className="voice-error">{error}</span>}
    </div>
  );
}

export default VoiceInput;
