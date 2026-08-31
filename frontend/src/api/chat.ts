export interface ChatReply {
  reply: string
}

export async function sendChatMessage(message: string): Promise<ChatReply> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {
      // response wasn't JSON - keep the generic message
    }
    throw new Error(detail)
  }

  return res.json() as Promise<ChatReply>
}
