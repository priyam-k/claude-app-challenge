import { useState, useEffect } from 'react'

function MarkdownText({ text }) {
  // Simple markdown parser for bold, italic, and line breaks
  const formatText = (str) => {
    const parts = []
    let currentIndex = 0

    // Match **bold**, *italic*, and newlines
    const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|\n)/g
    let match

    while ((match = regex.exec(str)) !== null) {
      // Add text before the match
      if (match.index > currentIndex) {
        parts.push({ type: 'text', content: str.slice(currentIndex, match.index) })
      }

      const matched = match[0]
      if (matched === '\n') {
        parts.push({ type: 'br' })
      } else if (matched.startsWith('**')) {
        parts.push({ type: 'bold', content: matched.slice(2, -2) })
      } else if (matched.startsWith('*')) {
        parts.push({ type: 'italic', content: matched.slice(1, -1) })
      }

      currentIndex = match.index + matched.length
    }

    // Add remaining text
    if (currentIndex < str.length) {
      parts.push({ type: 'text', content: str.slice(currentIndex) })
    }

    return parts
  }

  const parts = formatText(text)

  return (
    <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
      {parts.map((part, idx) => {
        if (part.type === 'bold') {
          return <strong key={idx} className="font-bold text-gray-900">{part.content}</strong>
        } else if (part.type === 'italic') {
          return <em key={idx} className="italic">{part.content}</em>
        } else if (part.type === 'br') {
          return <br key={idx} />
        } else {
          return <span key={idx}>{part.content}</span>
        }
      })}
    </div>
  )
}

export default function CampusCompass() {
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [events, setEvents] = useState([])
  const [showEvents, setShowEvents] = useState(true)

  useEffect(() => {
    // Fetch upcoming events on load
    fetch('http://localhost:8000/api/events/upcoming')
      .then(res => res.json())
      .then(data => setEvents(data.events || []))
      .catch(err => console.error('Error fetching events:', err))
  }, [])

  const exampleQueries = [
    "Where can I get vegetarian food near McKeldin right now?",
    "What shuttle do I take to get to Iribe at 2:30?",
    "What events are happening on campus this weekend?",
  ]

  const handleAsk = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/compass/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      const data = await response.json()
      setAnswer(data.answer)
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to get answer. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-xl p-8 mb-8 border border-gray-100">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl">
            <span className="text-3xl">🧭</span>
          </div>
          <div>
            <h2 className="text-3xl font-bold text-gray-800">Campus Compass</h2>
            <p className="text-gray-600">Your guide to dining, transportation, and campus events</p>
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6">
          <p className="text-sm font-semibold text-green-900 mb-2">💡 Try asking:</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {exampleQueries.map((ex, i) => (
              <button
                key={i}
                onClick={() => setQuery(ex)}
                className="text-left px-3 py-2 text-sm bg-white hover:bg-green-100 text-green-800 rounded-lg transition-colors border border-green-200"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
            placeholder="Ask about dining, buses, or events..."
            className="flex-1 px-6 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-lg transition-all"
          />
          <button
            onClick={handleAsk}
            disabled={loading}
            className="px-8 py-4 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-xl hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                Thinking...
              </span>
            ) : (
              'Ask'
            )}
          </button>
        </div>
      </div>

      {answer && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden mb-8">
          <div className="bg-gradient-to-r from-green-500 to-green-600 px-6 py-4">
            <h3 className="font-bold text-xl text-white flex items-center gap-2">
              <span className="text-2xl">💡</span>
              Answer
            </h3>
          </div>
          <div className="p-6">
            <MarkdownText text={answer} />
          </div>
        </div>
      )}

      {/* Upcoming Events Section */}
      {events.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-green-500 to-green-600 px-6 py-4 flex items-center justify-between">
            <h3 className="font-bold text-xl text-white flex items-center gap-2">
              <span className="text-2xl">📅</span>
              Upcoming Campus Events
            </h3>
            <button
              onClick={() => setShowEvents(!showEvents)}
              className="text-white hover:bg-white/20 px-3 py-1 rounded-lg transition-colors"
            >
              {showEvents ? '▼ Hide' : '▶ Show'}
            </button>
          </div>

          {showEvents && (
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              {events.map((event, idx) => (
                <div key={idx} className="group p-5 bg-gradient-to-br from-green-50 to-white rounded-xl border-2 border-green-100 hover:border-green-400 hover:shadow-lg transition-all">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg flex items-center justify-center font-bold text-lg">
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-lg text-gray-800 group-hover:text-green-600 transition-colors mb-2">
                        {event.title}
                      </h4>

                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2 text-gray-600">
                          <span className="text-lg">📅</span>
                          <span>{event.date}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600">
                          <span className="text-lg">📍</span>
                          <span>{event.location}</span>
                        </div>
                        {event.category && (
                          <span className="inline-block px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">
                            {event.category}
                          </span>
                        )}
                        {event.description && (
                          <p className="text-gray-600 mt-2">{event.description}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
