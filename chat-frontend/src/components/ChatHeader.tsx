import React from 'react'

type Props = { open: boolean; onToggle: () => void }

function WorldBankIcon() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M3 19h18M5 19V9l7-6 7 6v10" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M9 19v-4h6v4" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="12" cy="11" r="1.5" fill="white" opacity="0.7"/>
    </svg>
  )
}

export default function ChatHeader({ open, onToggle }: Props) {
  return (
    <div className="chat-header">
      {/* Subtle wave decoration */}
      <svg
        className="header-wave"
        viewBox="0 0 380 10"
        preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M0 5 Q95 -2, 190 5 T380 5 L380 10 L0 10 Z"
          fill="rgba(255,255,255,0.06)"
        />
      </svg>

      <div className="chat-header-left">
        <div className="chat-avatar-square">
          <WorldBankIcon />
        </div>
        <div className="chat-header-info">
          <span className="chat-title">World Bank</span>
          <span className="chat-name">WB Assistant</span>
          <span className="chat-header-status">
            <span className="online-dot" />
            En ligne · Données 2014–2023
          </span>
        </div>
      </div>

      <div className="chat-header-right">
        {/* Clear conversation */}
        <button
          className="chat-header-btn"
          aria-label="Réinitialiser la conversation"
          onClick={() => dispatchAction('clear')}
          title="Réinitialiser"
        >
          🗑
          <span className="chat-tooltip">Réinitialiser</span>
        </button>
        {/* Minimize / expand */}
        <button
          className="chat-header-btn"
          onClick={onToggle}
          aria-pressed={open}
          title={open ? 'Réduire' : 'Ouvrir'}
        >
          {open ? '▾' : '▴'}
          <span className="chat-tooltip">{open ? 'Réduire' : 'Ouvrir'}</span>
        </button>
      </div>
    </div>
  )
}

function dispatchAction(type: string) {
  try {
    window.dispatchEvent(new CustomEvent('chat-header-action', { detail: { type } }))
  } catch (err) {
    console.warn('Unable to dispatch action', err)
  }
}
