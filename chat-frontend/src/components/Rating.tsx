import React from 'react'

type Props = {
  onRate: (rating: 'up' | 'down') => void
}

export default function Rating({ onRate }: Props) {
  return (
    <div className="rating">
      <span className="rating-notice">Assistant IA – évitez de partager vos données personnelles.</span>
    </div>
  )
}
