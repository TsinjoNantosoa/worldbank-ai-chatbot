import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import DOMPurify from 'dompurify'
import { motion, AnimatePresence } from 'framer-motion'

import ChatHeader from './ChatHeader'
import MessageBubble from './MessageBubble'
import QuickReplies from './QuickReplies'
import Composer from './Composer'
import TypingIndicator from './TypingIndicator'
import DynamicSuggestions from './DynamicSuggestions'
import Rating from './Rating'
import { t, type Language } from '../i18n/translations'

/* ─── Types ──────────────────────────────────────────────────────── */
type Message = {
  id: string
  role: 'user' | 'bot'
  html: string
  sources?: string[]
}

type Reply = { icon: string; label: string }

/* ─── Greeting ───────────────────────────────────────────────────── */
function makeGreeting(lang: Language): Message {
  return {
    id: 'bot-greeting',
    role: 'bot',
    html: `
      <p>${t(lang, 'greetingIntro')}</p>
      <p style="margin-top:6px">${t(lang, 'greetingDetails')}</p>
      <p style="margin-top:6px;font-size:12px;color:#7a9ab8">${t(lang, 'greetingPrompt')}</p>
    `,
  }
}

/* ─── Component ──────────────────────────────────────────────────── */
export default function ChatWidget({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [lang, setLang] = useState<Language>(() => (localStorage.getItem('wb_lang') as Language) || 'fr')
  const [open, setOpen] = useState(false)
  const [showCallout, setShowCallout] = useState(true)
  const [messages, setMessages] = useState<Message[]>([makeGreeting(lang)])
  const [sessionId] = useState(() => 'wb-' + Math.random().toString(36).slice(2, 10))
  const [quickReplies, setQuickReplies] = useState<Reply[]>(t(lang, 'quickReplies'))
  const [quickRepliesVisible, setQuickRepliesVisible] = useState(true)
  const [isTyping, setIsTyping] = useState(false)
  const [suggestions, setSuggestions] = useState<Reply[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const listRef = useRef<HTMLDivElement | null>(null)

  /* ── Restore history ──────────────────────────────────────────── */
  useEffect(() => {
    axios
      .get(`${apiBaseUrl}/history`, { params: { session_id: sessionId } })
      .then((r) => {
        const history: Array<{ role: string; content: string }> = r.data?.history ?? []
        if (history.length > 0) {
          const msgs: Message[] = history.map((h, i) => ({
            id: `h-${i}`,
            role: h.role === 'user' ? 'user' : 'bot',
            html: DOMPurify.sanitize(h.content),
          }))
          setMessages(msgs)
        }
      })
      .catch(() => {/* no history yet – keep greeting */})
  }, [])

  /* ── Header actions (clear, lang-change) ──────────────────────── */
  useEffect(() => {
    function onAction(e: Event) {
      const detail = (e as CustomEvent).detail
      const type = detail?.type
      if (type === 'clear') {
        setMessages([makeGreeting(lang)])
        setSuggestions([])
        setShowSuggestions(false)
        setQuickReplies(t(lang, 'quickReplies'))
        setQuickRepliesVisible(true)
      } else if (type === 'lang-change') {
        const newLang = detail.lang as Language
        setLang(newLang)
        // Régénérer le message de bienvenue dans la nouvelle langue
        setMessages((prev) => {
          if (prev.length === 1 && prev[0].id === 'bot-greeting') {
            return [makeGreeting(newLang)]
          }
          return prev
        })
        setQuickReplies(t(newLang, 'quickReplies'))
        setQuickRepliesVisible(true)
      }
    }
    window.addEventListener('chat-header-action', onAction)
    return () => window.removeEventListener('chat-header-action', onAction)
  }, [lang])

  /* ── Auto-scroll ─────────────────────────────────────────────── */
  useEffect(() => {
    if (!open) return
    const el = listRef.current
    if (!el) return
    const raf = requestAnimationFrame(() => {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
    })
    return () => cancelAnimationFrame(raf)
  }, [messages, isTyping, open])

  /* ── Hide callout on open ─────────────────────────────────────── */
  useEffect(() => {
    if (open) setShowCallout(false)
  }, [open])

  /* ── Send message ─────────────────────────────────────────────── */
  async function sendText(text: string) {
    const userMsg: Message = {
      id: 'u-' + Date.now(),
      role: 'user',
      html: DOMPurify.sanitize(text),
    }
    setMessages((m) => [...m, userMsg])
    setQuickReplies([])
    setQuickRepliesVisible(false)
    setSuggestions([])
    setShowSuggestions(false)
    setIsTyping(true)

    try {
      const response = await axios.post(
        `${apiBaseUrl}/query`,
        { query: text, user_id: sessionId, lang },
        { timeout: 60_000 }
      )
      const data = response.data
      const botMsg: Message = {
        id: 'b-' + Date.now(),
        role: 'bot',
        html: DOMPurify.sanitize(data.answer ?? data.response ?? t(lang, 'noResponse')),
        sources: data.sources ?? [],
      }
      setMessages((m) => [...m, botMsg])
      setSuggestions(buildSuggestions(text, botMsg.html))
      setShowSuggestions(false)
    } catch (err: any) {
      const errMsg: Message = {
        id: 'err-' + Date.now(),
        role: 'bot',
        html: `<p style="color:#c0392b">${t(lang, 'errorMessage')}<br/><small>${err?.message ?? ''}</small></p>`,
      }
      setMessages((m) => [...m, errMsg])
    } finally {
      setIsTyping(false)
    }
  }

  /* ── Contextual suggestions ───────────────────────────────────── */
  function buildSuggestions(query: string, answer: string): Reply[] {
    const q = query.toLowerCase()
    const pool: Reply[] = t(lang, 'contextualSuggestions')
    // exclude questions similar to current
    const filtered = pool.filter(
      (s) => !s.label.toLowerCase().includes(q.slice(0, 8))
    )
    return filtered.slice(0, 3)
  }

  /* ── FAB ─────────────────────────────────────────────────────── */
  if (!open) {
    return (
      <motion.div
        className="chat-fab-wrapper"
        initial={{ opacity: 0, scale: 0.6, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
      >
        <AnimatePresence>
          {showCallout && (
            <motion.div
              className="chat-callout"
              initial={{ opacity: 0, y: 14, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 14, scale: 0.9 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              onClick={() => setOpen(true)}
            >
              <div className="chat-callout-text">
                {lang === 'fr'
                  ? (<>Des questions sur les données mondiales ?<br/><strong>WB Assistant est là pour vous.</strong></>)
                  : (<>Questions about global data?<br/><strong>WB Assistant is here for you.</strong></>)
                }
              </div>
              <button
                className="chat-callout-close"
                onClick={(e) => { e.stopPropagation(); setShowCallout(false) }}
                aria-label="Close"
              >×</button>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          className="chat-fab"
          onClick={() => setOpen(true)}
          aria-label={t(lang, 'open')}
        >
          <div className="chat-fab-pulse" />
          <div className="chat-fab-content">
            <div className="fab-wb-box">WB</div>
            <div className="chat-fab-text">WORLD<br/>BANK</div>
          </div>
          <div className="chat-fab-badge">1</div>
        </button>
      </motion.div>
    )
  }

  /* ── Widget open ─────────────────────────────────────────────── */
  return (
    <motion.div
      className="chat-widget open"
      initial={{ opacity: 0, y: 40, scale: 0.92 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Header */}
      <ChatHeader open={open} onToggle={() => setOpen(false)} />

      {/* Body */}
      <div className="chat-body">
        {/* Message list */}
        <div className="message-list" ref={listRef}>
          {messages.map((msg, i) => (
            <MessageBubble key={msg.id} message={msg} index={i} />
          ))}

          {/* Quick replies inside message area (like AAA - vertical pills) */}
          {quickRepliesVisible && quickReplies.length > 0 && (
            <div style={{ marginTop: 4 }}>
              <div style={{ fontSize: 12, color: '#5a7a99', fontWeight: 600, marginBottom: 6 }}>
                {lang === 'fr' ? 'Faites votre choix :' : 'Choose a topic:'}
              </div>
              <QuickReplies
                replies={quickReplies}
                onSelect={(text) => {
                  setQuickRepliesVisible(false)
                  setQuickReplies([])
                  sendText(text)
                }}
                layout="pills"
              />
            </div>
          )}

          {isTyping && <TypingIndicator />}
        </div>

        {/* Composer */}
        <Composer onSend={(txt) => {
          if (!txt.trim()) return
          setQuickRepliesVisible(false)
          setSuggestions([])
          setShowSuggestions(false)
          sendText(txt)
        }} lang={lang} />

        {/* Collapsible suggestions toggle (below composer like AAA) */}
        {suggestions.length > 0 && !isTyping && (
          <div className="suggestions-section">
            <button
              className="suggestions-toggle"
              onClick={() => setShowSuggestions((s) => !s)}
              aria-expanded={showSuggestions}
            >
              {showSuggestions
                ? (lang === 'fr' ? 'Masquer les suggestions' : 'Hide suggestions')
                : (lang === 'fr' ? 'Voir les suggestions' : 'View suggestions')
              }
            </button>
            {showSuggestions && (
              <DynamicSuggestions
                suggestions={suggestions}
                onSelect={(label) => {
                  setSuggestions([])
                  setShowSuggestions(false)
                  sendText(label)
                }}
              />
            )}
          </div>
        )}

        {/* Rating / disclaimer */}
        <Rating onRate={() => {}} />
      </div>
    </motion.div>
  )
}
