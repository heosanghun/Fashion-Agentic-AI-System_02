import React from 'react'
import './StatusBar.css'

function StatusBar({ progress, loading }) {
  if (!progress && !loading) {
    return null
  }

  const isSuccess = progress === '완료' || progress === '성공'
  const isFailed = progress === '실패'
  return (
    <div className={`status-bar ${loading ? 'loading' : ''} ${isSuccess ? 'status-done' : ''} ${isFailed ? 'status-failed' : ''}`} role="status" aria-live="polite">
      <div className="status-content">
        <span className="status-label">상태</span>
        {loading && <div className="spinner"></div>}
        <span>{progress || '처리 중...'}</span>
      </div>
      {loading && <div className="progress-bar">
        <div className="progress-fill"></div>
      </div>}
    </div>
  )
}

export default StatusBar

