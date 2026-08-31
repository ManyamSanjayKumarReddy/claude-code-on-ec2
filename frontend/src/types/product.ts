export interface Product {
  id: number
  name: string
  description: string | null
  price: string
  stock_quantity: number
  image_url: string | null
  created_at: string
  updated_at: string
}

export interface ProductInput {
  name: string
  description: string | null
  price: string
  stock_quantity: number
  image_url: string | null
}

export interface ProductPage {
  items: Product[]
  total: number
  page: number
  page_size: number
}
