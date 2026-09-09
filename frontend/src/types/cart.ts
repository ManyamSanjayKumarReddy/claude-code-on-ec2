export interface CartItem {
  product_id: number
  name: string
  price: string
  image_url: string | null
  quantity: number
  stock_quantity: number
  line_total: string
}

export interface Cart {
  items: CartItem[]
  total: string
  item_count: number
}
