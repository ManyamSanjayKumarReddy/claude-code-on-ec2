import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { Loader2, MessageCircle, Send, X } from 'lucide-react'

import { sendChatMessage } from '@/api/chat'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending, open])

  async function handleSend() {
    const text = input.trim()
    if (!text || sending) return

    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setSending(true)
    try {
      const { reply } = await sendChatMessage(text)
      setMessages((m) => [...m, { role: 'assistant', content: reply }])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong. Please try again.'
      setMessages((m) => [...m, { role: 'assistant', content: message }])
    } finally {
      setSending(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="fixed right-4 bottom-4 z-50 flex flex-col items-end gap-3">
      {open && (
        <div className="flex h-[28rem] w-80 flex-col overflow-hidden rounded-xl border bg-card text-card-foreground shadow-2xl sm:w-96">
          <div className="flex items-center justify-between gap-2 bg-gradient-to-r from-primary to-primary/80 px-4 py-3 text-primary-foreground">
            <div>
              <p className="font-heading text-sm font-semibold">Store Assistant</p>
              <p className="text-xs text-primary-foreground/80">Ask about our products</p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => setOpen(false)}
              className="text-primary-foreground hover:bg-primary-foreground/10 hover:text-primary-foreground"
              aria-label="Close chat"
            >
              <X />
            </Button>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Hi! Ask me about anything in the store's catalog — prices, stock, what we carry.
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                    m.role === 'user'
                      ? 'bg-gradient-to-r from-primary to-primary/80 text-primary-foreground'
                      : 'bg-muted text-foreground'
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                  <Loader2 className="size-3.5 animate-spin" /> Thinking...
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 border-t p-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about a product..."
              disabled={sending}
              aria-label="Chat message"
            />
            <Button
              type="button"
              size="icon"
              onClick={handleSend}
              disabled={sending || !input.trim()}
              className="shrink-0 bg-gradient-to-r from-primary to-primary/80 hover:opacity-90"
              aria-label="Send message"
            >
              <Send />
            </Button>
          </div>
        </div>
      )}

      <Button
        type="button"
        size="icon-lg"
        onClick={() => setOpen((o) => !o)}
        className="size-14 rounded-full bg-gradient-to-r from-primary to-primary/80 shadow-lg hover:opacity-90"
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? <X className="size-6" /> : <MessageCircle className="size-6" />}
      </Button>
    </div>
  )
}
