import React from 'react'
import { motion } from 'framer-motion'
import DOMPurify from 'dompurify'

type Message = {
  id: string
  role: 'user' | 'bot'
  html: string
  sources?: string[]
}

function getTime() {
  return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

function BotIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
      <path d="M3 3h18v14H3z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M3 17l4-4h14" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

export default function MessageBubble({
  message,
  index = 0,
}: {
  message: Message
  index?: number
}) {
  const safeHtml = DOMPurify.sanitize(message.html)

  return (
    <motion.div
      className={`message-row ${message.role}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.04 }}
    >
      {message.role === 'bot' && (
        <div className="bot-avatar-mini">
          <BotIcon />
        </div>
      )}
      <div className={`message-bubble ${message.role}`}>
        <div dangerouslySetInnerHTML={{ __html: safeHtml }} />
        <span className="msg-time">{getTime()}</span>
        {message.sources && message.sources.length > 0 && (
          <div className="message-sources">
            <small>Sources : </small>
            <ul style={{ margin: '3px 0 0', paddingLeft: 14 }}>
              {message.sources.map((s, i) => (
                <li key={i}>
                  <a href={s} target="_blank" rel="noreferrer">
                    {s}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </motion.div>
  )
}
