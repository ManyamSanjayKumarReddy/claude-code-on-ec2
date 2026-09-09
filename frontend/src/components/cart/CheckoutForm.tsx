import { useEffect, useState, type FormEvent } from 'react'

import { checkout, getShippingMethods } from '@/api/checkout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Cart } from '@/types/cart'
import type { Order, ShippingMethod } from '@/types/order'

interface CheckoutFormProps {
  cart: Cart
  onSuccess: (order: Order) => void
  onCancel: () => void
}

export function CheckoutForm({ cart, onSuccess, onCancel }: CheckoutFormProps) {
  const [methods, setMethods] = useState<ShippingMethod[]>([])
  const [methodCode, setMethodCode] = useState('')
  const [recipientName, setRecipientName] = useState('')
  const [addressLine1, setAddressLine1] = useState('')
  const [addressLine2, setAddressLine2] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [postalCode, setPostalCode] = useState('')
  const [country, setCountry] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getShippingMethods().then((fetched) => {
      setMethods(fetched)
      if (fetched.length > 0) setMethodCode(fetched[0].code)
    })
  }, [])

  const selectedMethod = methods.find((m) => m.code === methodCode)
  const total = Number(cart.total) + (selectedMethod ? Number(selectedMethod.cost) : 0)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const order = await checkout({
        recipient_name: recipientName,
        address_line1: addressLine1,
        address_line2: addressLine2.trim() === '' ? null : addressLine2.trim(),
        city,
        state,
        postal_code: postalCode,
        country,
        shipping_method: methodCode,
      })
      onSuccess(order)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="recipient_name">Full name</Label>
        <Input
          id="recipient_name"
          value={recipientName}
          onChange={(e) => setRecipientName(e.target.value)}
          required
          maxLength={200}
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="address_line1">Address</Label>
        <Input
          id="address_line1"
          value={addressLine1}
          onChange={(e) => setAddressLine1(e.target.value)}
          required
          maxLength={255}
          placeholder="Street address"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="address_line2">Address line 2 (optional)</Label>
        <Input
          id="address_line2"
          value={addressLine2}
          onChange={(e) => setAddressLine2(e.target.value)}
          maxLength={255}
          placeholder="Apt, suite, etc."
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="city">City</Label>
          <Input id="city" value={city} onChange={(e) => setCity(e.target.value)} required maxLength={100} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="state">State</Label>
          <Input id="state" value={state} onChange={(e) => setState(e.target.value)} required maxLength={100} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="postal_code">Postal code</Label>
          <Input
            id="postal_code"
            value={postalCode}
            onChange={(e) => setPostalCode(e.target.value)}
            required
            maxLength={20}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="country">Country</Label>
          <Input id="country" value={country} onChange={(e) => setCountry(e.target.value)} required maxLength={100} />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label className="text-xs text-muted-foreground">Shipping method</Label>
        <div className="flex flex-col gap-2">
          {methods.map((m) => (
            <button
              key={m.code}
              type="button"
              onClick={() => setMethodCode(m.code)}
              className={`flex items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                methodCode === m.code ? 'border-primary bg-primary/5' : 'hover:bg-muted'
              }`}
            >
              <span>{m.label}</span>
              <span className="font-medium">${m.cost}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-1 border-t pt-3 text-sm">
        <div className="flex justify-between text-muted-foreground">
          <span>Subtotal</span>
          <span>${cart.total}</span>
        </div>
        <div className="flex justify-between text-muted-foreground">
          <span>Shipping</span>
          <span>{selectedMethod ? `$${selectedMethod.cost}` : '—'}</span>
        </div>
        <div className="flex justify-between text-base font-semibold">
          <span>Total</span>
          <span>${total.toFixed(2)}</span>
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Back to cart
        </Button>
        <Button type="submit" disabled={submitting || !methodCode}>
          {submitting ? 'Placing order...' : 'Place order'}
        </Button>
      </div>
    </form>
  )
}
