import { useState, useRef, useEffect } from 'react';
import './SimplePromptBar.css';

function SimplePromptBar({
  text,
  setText,
  image,
  personImage,
  onImageChange,
  onPersonImageChange,
  onSubmit,
  loading,
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const garmentInputRef = useRef(null);
  const personInputRef = useRef(null);
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

  const handleAddGarment = () => {
    garmentInputRef.current?.click();
    setDropdownOpen(false);
  };
  const handleAddPerson = () => {
    personInputRef.current?.click();
    setDropdownOpen(false);
  };

  const handleGarmentChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onImageChange(file);
    } else if (file) alert('이미지 파일만 업로드 가능합니다.');
    e.target.value = '';
  };
  const handlePersonChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onPersonImageChange(file);
    } else if (file) alert('이미지 파일만 업로드 가능합니다.');
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
                onClick={handleAddGarment}
                role="menuitem"
              >
                <span className="simple-prompt-dropdown-icon">👕</span>
                입을 옷 사진 (의류)
              </button>
              <button
                type="button"
                className="simple-prompt-dropdown-item"
                onClick={handleAddPerson}
                role="menuitem"
              >
                <span className="simple-prompt-dropdown-icon">👤</span>
                내 사진 (인물)
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
          <input ref={garmentInputRef} type="file" accept="image/*" onChange={handleGarmentChange} style={{ display: 'none' }} aria-hidden="true" />
          <input ref={personInputRef} type="file" accept="image/*" onChange={handlePersonChange} style={{ display: 'none' }} aria-hidden="true" />
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
          <button
            type="button"
            className="simple-prompt-send"
            onClick={onSubmit}
            disabled={loading || (!text && !image && !personImage)}
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
      {(image || personImage) && (
        <div className="simple-prompt-attach-preview">
          {image && (
            <span className="simple-prompt-attach-preview-item">
              <img src={URL.createObjectURL(image)} alt="의류" />
              <span>👕 {image.name}</span>
              <button type="button" className="simple-prompt-attach-remove" onClick={() => onImageChange(null)} aria-label="의류 제거">×</button>
            </span>
          )}
          {personImage && (
            <span className="simple-prompt-attach-preview-item">
              <img src={URL.createObjectURL(personImage)} alt="인물" />
              <span>👤 {personImage.name}</span>
              <button type="button" className="simple-prompt-attach-remove" onClick={() => onPersonImageChange(null)} aria-label="인물 제거">×</button>
            </span>
          )}
          <p className="simple-prompt-attach-hint">가상 피팅: 의류 + 인물 두 장을 올리면 더 정확합니다.</p>
        </div>
      )}
    </section>
  );
}

export default SimplePromptBar;
