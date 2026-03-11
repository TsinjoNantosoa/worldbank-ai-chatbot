import React, { useState, useEffect } from 'react'
import { t, type Language } from '../i18n/translations'

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
  const [lang, setLang] = useState<Language>(() => (localStorage.getItem('wb_lang') as Language) || 'fr')

  useEffect(() => {
    localStorage.setItem('wb_lang', lang)
    dispatchAction('lang-change', { lang })
  }, [lang])

  const toggleLang = () => {
    setLang((prev) => (prev === 'fr' ? 'en' : 'fr'))
  }

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
          <span className="chat-title">{t(lang, 'chatTitle')}</span>
          <span className="chat-name">{t(lang, 'chatName')}</span>
          <span className="chat-header-status">
            <span className="online-dot" />
            {t(lang, 'statusOnline')}
          </span>
        </div>
      </div>

      <div className="chat-header-right">
        {/* Language toggle */}
        <button
          className="chat-header-btn lang-toggle"
          onClick={toggleLang}
          aria-label={lang === 'fr' ? t('en', 'switchToEnglish') : t('fr', 'switchToFrench')}
          title={lang === 'fr' ? 'English' : 'Français'}
        >
          <span className="lang-text">{lang === 'fr' ? 'EN' : 'FR'}</span>
          <span className="chat-tooltip">{lang === 'fr' ? 'English' : 'Français'}</span>
        </button>
        {/* Clear conversation */}
        <button
          className="chat-header-btn"
          aria-label={t(lang, 'clearConversation')}
          onClick={() => dispatchAction('clear')}
          title={t(lang, 'clearConversation')}
        >
          🗑
          <span className="chat-tooltip">{t(lang, 'clearConversation')}</span>
        </button>
        {/* Minimize / expand */}
        <button
          className="chat-header-btn"
          onClick={onToggle}
          aria-pressed={open}
          title={open ? t(lang, 'minimize') : t(lang, 'open')}
        >
          {open ? '▾' : '▴'}
          <span className="chat-tooltip">{open ? t(lang, 'minimize') : t(lang, 'open')}</span>
        </button>
      </div>
    </div>
  )
}

function dispatchAction(type: string, payload?: any) {
  try {
    window.dispatchEvent(new CustomEvent('chat-header-action', { detail: { type, ...payload } }))
  } catch (err) {
    console.warn('Unable to dispatch action', err)
  }
}
