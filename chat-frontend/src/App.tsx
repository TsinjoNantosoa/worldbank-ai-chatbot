import React from 'react'
import ChatWidget from './components/ChatWidget'

export default function App() {
  const apiBaseUrl = (import.meta as any).env.VITE_API_BASE_URL ?? 'http://localhost:8000'

  return (
    <div className="demo-page">
      {/* Demo landing page shown behind the widget */}
      <div className="demo-card">
        <div className="demo-logo">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
            <path d="M3 19h18M5 19V9l7-6 7 6v10M9 19v-4h6v4" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h1 className="demo-title">World Bank Data Chatbot</h1>
        <p className="demo-subtitle">
          Interrogez en langage naturel les indicateurs économiques, sociaux et environnementaux  
          de la&nbsp;<strong>Banque Mondiale</strong> — 1 171 entrées couvrant 35+ pays.
        </p>
        <div>
          <span className="demo-tag">📊 PIB &amp; croissance</span>
          <span className="demo-tag">👥 Population</span>
          <span className="demo-tag">🎓 Éducation</span>
          <span className="demo-tag">🏥 Santé</span>
          <span className="demo-tag">🌿 Environnement</span>
          <span className="demo-tag">💹 Commerce</span>
        </div>
      </div>
      {/* The actual chat widget (fixed bottom-right) */}
      <ChatWidget apiBaseUrl={apiBaseUrl} />
    </div>
  )
}
