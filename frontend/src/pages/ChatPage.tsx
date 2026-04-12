import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { postChat } from '../api/client'
import { useFilterStore } from '../store/filterStore'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

function buildExportUrl(base: string, filters: ReturnType<typeof useFilterStore.getState>): string {
  const params = new URLSearchParams()
  params.set('source', filters.source)
  if (filters.startDate) params.set('start_date', filters.startDate)
  if (filters.endDate) params.set('end_date', filters.endDate)
  params.set('min_magnitude', String(filters.minMagnitude))
  filters.alertLevels.forEach((l) => params.append('alert_levels[]', l))
  filters.countries.forEach((c) => params.append('countries[]', c))
  return `${base}?${params.toString()}`
}

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your earthquake data assistant. Ask me anything about recent seismic activity.',
    },
  ])
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const filters = useFilterStore()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const mutation = useMutation({
    mutationFn: postChat,
    onSuccess: (response) => {
      setMessages((prev) => [...prev, { role: 'assistant', content: response }])
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ])
    },
  })

  function sendMessage() {
    const text = input.trim()
    if (!text || mutation.isPending) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    mutation.mutate(text)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const filterState = useFilterStore.getState()

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-3xl mx-auto">
      {/* Export buttons */}
      <div className="flex gap-2 mb-3 shrink-0">
        <span className="text-xs text-gray-400 self-center mr-1">Export:</span>
        {[
          { label: 'PDF', path: '/api/v1/export/pdf' },
          { label: 'CSV', path: '/api/v1/export/csv' },
          { label: 'XML', path: '/api/v1/export/xml' },
        ].map(({ label, path }) => (
          <a
            key={label}
            href={buildExportUrl(`${API_BASE}${path}`, filterState)}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs rounded transition-colors"
          >
            {label}
          </a>
        ))}
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-3 pr-1">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {mutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-gray-400 rounded-lg px-4 py-2.5 text-sm italic">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="flex gap-2 shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about earthquake data..."
          className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2.5 text-sm border border-gray-600 focus:outline-none focus:border-blue-500 placeholder-gray-400"
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || mutation.isPending}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  )
}
