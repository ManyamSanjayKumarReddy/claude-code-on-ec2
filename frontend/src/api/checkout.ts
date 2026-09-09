import type { CheckoutInput, Order, ShippingMethod } from '@/types/order'

const CHECKOUT_URL = '/api/checkout'
const ORDERS_URL = '/api/orders'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail || `Request failed with status ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function getShippingMethods(): Promise<ShippingMethod[]> {
  return fetch(`${CHECKOUT_URL}/shipping-methods`).then((res) => handle<ShippingMethod[]>(res))
}

export function checkout(input: CheckoutInput): Promise<Order> {
  return fetch(CHECKOUT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(input),
  }).then((res) => handle<Order>(res))
}

export function getOrders(): Promise<Order[]> {
  return fetch(ORDERS_URL, { credentials: 'include' }).then((res) => handle<Order[]>(res))
}
