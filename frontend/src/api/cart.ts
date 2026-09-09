import type { Cart } from '@/types/cart'

const BASE_URL = '/api/cart'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail || `Request failed with status ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function getCart(): Promise<Cart> {
  return fetch(BASE_URL, { credentials: 'include' }).then((res) => handle<Cart>(res))
}

export function addToCart(productId: number, quantity = 1): Promise<Cart> {
  return fetch(`${BASE_URL}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ product_id: productId, quantity }),
  }).then((res) => handle<Cart>(res))
}

export function updateCartItem(productId: number, quantity: number): Promise<Cart> {
  return fetch(`${BASE_URL}/items/${productId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ quantity }),
  }).then((res) => handle<Cart>(res))
}

export function removeFromCart(productId: number): Promise<Cart> {
  return fetch(`${BASE_URL}/items/${productId}`, {
    method: 'DELETE',
    credentials: 'include',
  }).then((res) => handle<Cart>(res))
}
