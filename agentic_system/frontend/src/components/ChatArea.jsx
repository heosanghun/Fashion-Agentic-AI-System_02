import './ChatArea.css';

function ChatArea({ messages }) {
  if (!messages || messages.length === 0) {
    return (
      <div className="chat-area">
        <div className="chat-placeholder">
          <p>질문을 입력하면 여기에 답변이 표시됩니다.</p>
          <p className="chat-placeholder-hint">가상 피팅을 실행하려면 &quot;Try-On 실행해줘&quot;라고 말해 주세요.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-area" role="log" aria-live="polite">
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble chat-bubble-${msg.role}`}>
            <div className="chat-bubble-inner">
              {msg.role === 'user' && <span className="chat-role-label">나</span>}
              {msg.role === 'assistant' && <span className="chat-role-label">AI</span>}
              {msg.role === 'assistant' && msg.openaiError && (
                <div className="chat-openai-notice" role="status">
                  ⚠ OpenAI API를 사용할 수 없습니다. 아래는 기본 안내 문구입니다.
                  <span className="chat-openai-detail">{msg.openaiError}</span>
                </div>
              )}
              <div className="chat-bubble-content">
                {msg.content}
                {msg.imageName && (
                  <span className="chat-attach-badge">📎 {msg.imageName}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ChatArea;
