import { useState, useRef, useEffect } from 'react';
import VoiceInput from './VoiceInput';
import './SimplePromptBar.css';

function SimplePromptBar({
  text,
  setText,
  image,
  onImageChange,
  onSubmit,
  loading,
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const fileInputRef = useRef(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const close = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener('click', close);
      return () => document.removeEventListener('click', close);
    }
  }, [dropdownOpen]);

  const handleAddPhoto = () => {
    fileInputRef.current?.click();
    setDropdownOpen(false);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onImageChange(file);
    } else if (file) {
      alert('이미지 파일만 업로드 가능합니다.');
    }
    e.target.value = '';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <section className="simple-prompt" aria-label="프롬프트 입력">
      <h2 className="simple-prompt-title">무엇을 도와드릴까요?</h2>
      <div className="simple-prompt-bar">
        <div className="simple-prompt-bar-left" ref={dropdownRef}>
          <button
            type="button"
            className="simple-prompt-plus"
            onClick={() => setDropdownOpen((o) => !o)}
            disabled={loading}
            aria-expanded={dropdownOpen}
            aria-haspopup="true"
            aria-label="추가 옵션"
          >
            <span aria-hidden="true">+</span>
          </button>
          {dropdownOpen && (
            <div className="simple-prompt-dropdown" role="menu">
              <button
                type="button"
                className="simple-prompt-dropdown-item"
                onClick={handleAddPhoto}
                role="menuitem"
              >
                <span className="simple-prompt-dropdown-icon">📎</span>
                사진 및 파일 추가
              </button>
              <button type="button" className="simple-prompt-dropdown-item disabled" disabled role="menuitem">
                <span className="simple-prompt-dropdown-icon">🖼️</span>
                이미지 만들기
              </button>
              <button type="button" className="simple-prompt-dropdown-item disabled" disabled role="menuitem">
                <span className="simple-prompt-dropdown-icon">🔬</span>
                Deep Research
              </button>
              <button type="button" className="simple-prompt-dropdown-item disabled" disabled role="menuitem">
                <span className="simple-prompt-dropdown-icon">🛒</span>
                쇼핑 어시스턴트
              </button>
              <button type="button" className="simple-prompt-dropdown-item disabled" disabled role="menuitem">
                <span className="simple-prompt-dropdown-icon">🌐</span>
                웹 검색
              </button>
              <button type="button" className="simple-prompt-dropdown-item simple-prompt-dropdown-more" disabled role="menuitem">
                <span>⋯</span>
                <span>더 보기</span>
                <span className="simple-prompt-dropdown-arrow">→</span>
              </button>
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            aria-hidden="true"
          />
        </div>
        <input
          type="text"
          className="simple-prompt-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="무엇이든 물어보세요"
          disabled={loading}
          aria-label="메시지 입력"
        />
        <div className="simple-prompt-bar-right">
          <VoiceInput onTranscript={setText} disabled={loading} compact />
          <button
            type="button"
            className="simple-prompt-send"
            onClick={onSubmit}
            disabled={loading || (!text && !image)}
            aria-label="보내기"
            title="보내기"
          >
            {loading ? (
              <span className="simple-prompt-send-dots">
                <span /><span /><span />
              </span>
            ) : (
              <span className="simple-prompt-send-icon" aria-hidden="true">➤</span>
            )}
          </button>
        </div>
      </div>
      {image && (
        <div className="simple-prompt-attach-preview">
          <img src={URL.createObjectURL(image)} alt="첨부" />
          <span>{image.name}</span>
          <button
            type="button"
            className="simple-prompt-attach-remove"
            onClick={() => onImageChange(null)}
            aria-label="첨부 제거"
          >
            ×
          </button>
        </div>
      )}
    </section>
  );
}

export default SimplePromptBar;
