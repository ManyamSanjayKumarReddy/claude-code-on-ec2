import { useEffect, useState } from 'react'
import { PackageOpen } from 'lucide-react'

import { getOrders } from '@/api/checkout'
import { Badge } from '@/components/ui/badge'
import type { Order } from '@/types/order'

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOrders()
      .then(setOrders)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading orders...</p>
  }

  if (orders.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-16 text-center">
        <PackageOpen className="size-10 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No orders yet.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
      {orders.map((order) => (
        <div key={order.id} className="rounded-xl border p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-sm font-semibold">Order #{order.id}</p>
              <p className="text-xs text-muted-foreground">
                {new Date(order.created_at).toLocaleDateString()} &middot; Shipping to {order.city}, {order.state}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className="capitalize">
                {order.status}
              </Badge>
              <p className="text-sm font-semibold">${order.total}</p>
            </div>
          </div>
          <ul className="mt-3 flex flex-col gap-1 border-t pt-3 text-sm text-muted-foreground">
            {order.items.map((item, i) => (
              <li key={i} className="flex justify-between">
                <span>
                  {item.quantity} &times; {item.product_name}
                </span>
                <span>${item.unit_price}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
