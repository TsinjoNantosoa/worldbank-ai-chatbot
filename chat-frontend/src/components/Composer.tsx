import React, { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { motion } from 'framer-motion'
import { t, type Language } from '../i18n/translations'

type Props = { 
  onSend: (text: string) => void
  lang: Language
}

export default function Composer({ onSend, lang }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '24px'
    }
  }, [])

  function resize() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
    el.style.overflowY = el.scrollHeight > 120 ? 'auto' : 'hidden'
  }

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setValue(e.target.value)
    resize()
  }

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    const text = value.trim()
    if (!text) return
    onSend(text)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = '24px'
    }
  }

  return (
    <div className="composer-zone">
      <div className="composer-row">
        <textarea
          ref={textareaRef}
          className="composer-input"
          placeholder={t(lang, 'composerPlaceholder')}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKey}
          rows={1}
        />
        <motion.button
          className="composer-send-btn"
          onClick={submit}
          aria-label={t(lang, 'sendButton')}
          title={t(lang, 'sendButton')}
          type="button"
          whileHover={{ scale: 1.07 }}
          whileTap={{ scale: 0.93 }}
        >
          ➤
        </motion.button>
      </div>
      <div className="composer-footer">
        Powered by World Bank Open Data · RAG + OpenAI
      </div>
    </div>
  )
}
