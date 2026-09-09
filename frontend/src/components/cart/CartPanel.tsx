import { Minus, Plus, ShoppingCart, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { Cart } from '@/types/cart'

interface CartPanelProps {
  cart: Cart | null
  onUpdateQuantity: (productId: number, quantity: number) => void
  onRemove: (productId: number) => void
}

export function CartPanel({ cart, onUpdateQuantity, onRemove }: CartPanelProps) {
  if (!cart || cart.items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-center">
        <ShoppingCart className="size-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Your cart is empty.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex max-h-[50vh] flex-col gap-3 overflow-y-auto">
        {cart.items.map((item) => (
          <div key={item.product_id} className="flex items-center gap-3 border-b pb-3 last:border-b-0 last:pb-0">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{item.name}</p>
              <p className="text-xs text-muted-foreground">${item.price} each</p>
            </div>
            <div className="flex items-center gap-1">
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                onClick={() => onUpdateQuantity(item.product_id, item.quantity - 1)}
                disabled={item.quantity <= 1}
                aria-label="Decrease quantity"
              >
                <Minus />
              </Button>
              <span className="w-6 text-center text-sm">{item.quantity}</span>
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                onClick={() => onUpdateQuantity(item.product_id, item.quantity + 1)}
                disabled={item.quantity >= item.stock_quantity}
                aria-label="Increase quantity"
              >
                <Plus />
              </Button>
            </div>
            <p className="w-16 shrink-0 text-right text-sm font-medium">${item.line_total}</p>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={() => onRemove(item.product_id)}
              className="text-destructive hover:bg-destructive/10 hover:text-destructive"
              aria-label="Remove item"
            >
              <Trash2 />
            </Button>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between border-t pt-3">
        <p className="text-sm text-muted-foreground">
          {cart.item_count} item{cart.item_count === 1 ? '' : 's'}
        </p>
        <p className="text-lg font-semibold">${cart.total}</p>
      </div>
    </div>
  )
}
