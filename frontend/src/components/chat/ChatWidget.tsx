import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { Loader2, MessageCircle, PackageOpen, Send, X } from 'lucide-react'

import { sendChatMessage, type ChatProductRef } from '@/api/chat'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: ChatProductRef[]
}

function ChatProductCard({ product }: { product: ChatProductRef }) {
  const [imageFailed, setImageFailed] = useState(false)
  const showImage = product.image_url && !imageFailed

  return (
    <div className="flex w-28 shrink-0 flex-col gap-1 rounded-lg border bg-background p-2">
      {showImage ? (
        <img
          src={product.image_url!}
          alt={product.name}
          className="aspect-square w-full rounded-md object-cover"
          loading="lazy"
          onError={() => setImageFailed(true)}
        />
      ) : (
        <div className="flex aspect-square w-full items-center justify-center rounded-md bg-muted">
          <PackageOpen className="size-6 text-muted-foreground" />
        </div>
      )}
      <p className="line-clamp-2 text-[11px] font-medium">{product.name}</p>
      <p className="text-[11px] text-muted-foreground">${product.price}</p>
    </div>
  )
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
      const { reply, products } = await sendChatMessage(text)
      setMessages((m) => [...m, { role: 'assistant', content: reply, products }])
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
        <div className="flex h-[75vh] max-h-[720px] w-[420px] max-w-[92vw] flex-col overflow-hidden rounded-xl border bg-card text-card-foreground shadow-2xl">
          <div className="flex items-center justify-between gap-2 bg-primary px-4 py-3 text-primary-foreground">
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
              <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                    m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
                  }`}
                >
                  {m.content}
                </div>
                {m.products && m.products.length > 0 && (
                  <div className="mt-2 flex max-w-full gap-2 overflow-x-auto pb-1">
                    {m.products.map((p) => (
                      <ChatProductCard key={p.id} product={p} />
                    ))}
                  </div>
                )}
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
              className="shrink-0"
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
        className="size-14 rounded-full shadow-lg"
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? <X className="size-6" /> : <MessageCircle className="size-6" />}
      </Button>
    </div>
  )
}
