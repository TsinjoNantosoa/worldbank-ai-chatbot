import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'

type Suggestion = { icon: string; label: string }
type Props = { suggestions: Suggestion[]; onSelect: (label: string) => void }

export default function DynamicSuggestions({ suggestions, onSelect }: Props) {
  if (!suggestions || suggestions.length === 0) return null
  return (
    <motion.div
      className="dynamic-suggestions"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
    >
      <div className="suggestion-list">
        {suggestions.map((s, i) => (
          <motion.button
            key={i}
            className="suggestion-chip"
            onClick={() => onSelect(s.label)}
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.07, duration: 0.18 }}
            whileHover={{ scale: 1.04, y: -2 }}
            whileTap={{ scale: 0.96 }}
          >
            <span>{s.icon}</span>
            <span>{s.label}</span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}
