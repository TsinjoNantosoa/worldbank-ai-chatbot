import React from 'react'

type Reply = { icon: string; label: string }
type Props = {
  replies: Reply[]
  onSelect: (text: string) => void
  layout?: 'grid' | 'list' | 'cards' | 'pills'
}

export default function QuickReplies({ replies, onSelect, layout = 'grid' }: Props) {
  if (!replies || replies.length === 0) return null
  return (
    <div className={`quick-replies ${layout === 'list' || layout === 'pills' ? 'vertical' : ''}`}>
      {replies.map((r, i) => (
        <button
          key={i}
          className="quick-reply-btn"
          onClick={() => onSelect(r.label)}
          aria-label={r.label}
        >
          <span>{r.icon}</span>
          <span>{r.label}</span>
        </button>
      ))}
    </div>
  )
}
