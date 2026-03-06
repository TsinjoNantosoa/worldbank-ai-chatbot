import React from 'react'
import { motion } from 'framer-motion'

export default function TypingIndicator() {
  return (
    <div className="message-row bot typing-row">
      <div className="bot-avatar-mini">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M3 3h18v14H3z" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M3 17l4-4h14" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      <div className="typing-indicator">
        <span className="typing-text">WB Assistant répond…</span>
        <div className="typing-dots">
          {[0, 0.2, 0.4].map((delay, i) => (
            <motion.span
              key={i}
              className="dot"
              animate={{ opacity: [0.3, 1, 0.3], scaleY: [0.6, 1, 0.6] }}
              transition={{ duration: 1.2, repeat: Infinity, delay }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
