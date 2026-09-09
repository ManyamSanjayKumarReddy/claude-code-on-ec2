export interface ShippingMethod {
  code: string
  label: string
  cost: string
}

export interface CheckoutInput {
  recipient_name: string
  address_line1: string
  address_line2: string | null
  city: string
  state: string
  postal_code: string
  country: string
  shipping_method: string
}

export interface OrderItem {
  product_name: string
  unit_price: string
  quantity: number
}

export interface Order {
  id: number
  status: string
  recipient_name: string
  address_line1: string
  address_line2: string | null
  city: string
  state: string
  postal_code: string
  country: string
  shipping_method: string
  shipping_cost: string
  subtotal: string
  total: string
  created_at: string
  items: OrderItem[]
}
