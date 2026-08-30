export interface Product {
  id: number
  name: string
  description: string | null
  price: string
  stock_quantity: number
  created_at: string
  updated_at: string
}

export interface ProductInput {
  name: string
  description: string | null
  price: string
  stock_quantity: number
}
