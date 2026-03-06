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

/* ─── Types ──────────────────────────────────────────────────────── */
type Message = {
  id: string
  role: 'user' | 'bot'
  html: string
  sources?: string[]
}

type Reply = { icon: string; label: string }

/* ─── Suggestions defaults ───────────────────────────────────────── */
const DEFAULT_QUICK_REPLIES: Reply[] = [
  { icon: '📊', label: 'PIB de la France en 2023' },
  { icon: '🌍', label: 'Population mondiale 2023' },
  { icon: '💹', label: 'Croissance économique USA' },
  { icon: '🎓', label: 'Taux de scolarisation en Afrique' },
  { icon: '🌿', label: 'Émissions CO₂ par pays' },
]

/* ─── Greeting ───────────────────────────────────────────────────── */
function makeGreeting(): Message {
  return {
    id: 'bot-greeting',
    role: 'bot',
    html: `
      <p>Bonjour 👋 Je suis <strong>WB Assistant</strong>, votre guide des données de
      la <strong>Banque Mondiale</strong>.</p>
      <p style="margin-top:6px">Je peux vous renseigner sur le PIB, la croissance, 
      l'inflation, la population, l'éducation, la santé, l'énergie et plus encore,
      pour <strong>35+ pays</strong> de 2014 à 2023.</p>
      <p style="margin-top:6px;font-size:12px;color:#7a9ab8">Cliquez sur une suggestion ou posez 
      votre question ci-dessous.</p>
    `,
  }
}

/* ─── Component ──────────────────────────────────────────────────── */
export default function ChatWidget({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [open, setOpen] = useState(false)
  const [showCallout, setShowCallout] = useState(true)
  const [messages, setMessages] = useState<Message[]>([makeGreeting()])
  const [sessionId] = useState(() => 'wb-' + Math.random().toString(36).slice(2, 10))
  const [quickReplies, setQuickReplies] = useState<Reply[]>(DEFAULT_QUICK_REPLIES)
  const [isTyping, setIsTyping] = useState(false)
  const [suggestions, setSuggestions] = useState<Reply[]>([])
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

  /* ── Header actions (clear) ───────────────────────────────────── */
  useEffect(() => {
    function onAction(e: Event) {
      const type = (e as CustomEvent).detail?.type
      if (type === 'clear') {
        setMessages([makeGreeting()])
        setSuggestions([])
        setQuickReplies(DEFAULT_QUICK_REPLIES)
      }
    }
    window.addEventListener('chat-header-action', onAction)
    return () => window.removeEventListener('chat-header-action', onAction)
  }, [])

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
    setSuggestions([])
    setIsTyping(true)

    try {
      const response = await axios.post(
        `${apiBaseUrl}/query`,
        { query: text, user_id: sessionId, lang: 'fr' },
        { timeout: 60_000 }
      )
      const data = response.data
      const botMsg: Message = {
        id: 'b-' + Date.now(),
        role: 'bot',
        html: DOMPurify.sanitize(data.answer ?? data.response ?? 'Désolé, pas de réponse.'),
        sources: data.sources ?? [],
      }
      setMessages((m) => [...m, botMsg])
      setSuggestions(buildSuggestions(text, botMsg.html))
    } catch (err: any) {
      const errMsg: Message = {
        id: 'err-' + Date.now(),
        role: 'bot',
        html: `<p style="color:#c0392b">⚠️ Erreur : impossible de joindre le serveur.<br/><small>${err?.message ?? ''}</small></p>`,
      }
      setMessages((m) => [...m, errMsg])
    } finally {
      setIsTyping(false)
    }
  }

  /* ── Contextual suggestions ───────────────────────────────────── */
  function buildSuggestions(query: string, answer: string): Reply[] {
    const q = query.toLowerCase()
    const pool: Reply[] = [
      { icon: '📈', label: 'Quelle est la croissance du PIB de la Chine ?' },
      { icon: '💹', label: 'Quel est le taux d\'inflation en Inde ?' },
      { icon: '👥', label: 'Quelle est la population du Brésil ?' },
      { icon: '🏥', label: 'Quel est le taux de mortalité infantile au Nigeria ?' },
      { icon: '🎓', label: 'Quel est le taux de scolarisation au Maroc ?' },
      { icon: '⚡', label: 'Consommation d\'énergie per capita au Japon ?' },
      { icon: '🌳', label: 'Quelle est la superficie forestière en Russie ?' },
      { icon: '📱', label: 'Taux d\'internet en Afrique ?' },
      { icon: '📊', label: 'PIB per capita de l\'Allemagne ?' },
      { icon: '🌍', label: 'Taux de chômage en Espagne ?' },
    ]
    // exclude questions similar to current
    const filtered = pool.filter(
      (s) => !s.label.toLowerCase().includes(q.slice(0, 8))
    )
    return filtered.slice(0, 3)
  }

  /* ── FAB ─────────────────────────────────────────────────────── */
  if (!open) {
    return (
      <>
        {showCallout && (
          <motion.div
            className="chat-callout"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
          >
            💬 Posez vos questions sur la Banque Mondiale
          </motion.div>
        )}
        <motion.button
          className="chat-fab"
          onClick={() => setOpen(true)}
          title="Ouvrir le chat"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 260, damping: 20 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path
              d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
              stroke="white" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"
            />
            <path d="M8 10h8M8 14h5" stroke="white" strokeWidth="1.7" strokeLinecap="round"/>
          </svg>
        </motion.button>
      </>
    )
  }

  /* ── Widget open ─────────────────────────────────────────────── */
  return (
    <motion.div
      className="chat-widget open"
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
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
          {isTyping && <TypingIndicator />}
        </div>

        {/* Dynamic suggestions after bot replies */}
        <AnimatePresence>
          {suggestions.length > 0 && !isTyping && (
            <DynamicSuggestions
              suggestions={suggestions}
              onSelect={(label) => {
                setSuggestions([])
                sendText(label)
              }}
            />
          )}
        </AnimatePresence>

        {/* Quick replies (shown at start) */}
        {quickReplies.length > 0 && (
          <QuickReplies
            replies={quickReplies}
            onSelect={(text) => {
              setQuickReplies([])
              sendText(text)
            }}
          />
        )}

        {/* Rating / disclaimer */}
        <Rating onRate={() => {}} />

        {/* Composer */}
        <Composer onSend={sendText} />
      </div>
    </motion.div>
  )
}
