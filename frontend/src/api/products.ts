import type { Product, ProductInput, ProductPage } from '@/types/product'

const BASE_URL = '/api/products'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Request failed with status ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export interface ProductFilters {
  search?: string
  minPrice?: string
  maxPrice?: string
  inStock?: boolean
}

export function listProducts(page = 1, pageSize = 20, filters: ProductFilters = {}): Promise<ProductPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (filters.search) params.set('search', filters.search)
  if (filters.minPrice) params.set('min_price', filters.minPrice)
  if (filters.maxPrice) params.set('max_price', filters.maxPrice)
  if (filters.inStock !== undefined) params.set('in_stock', String(filters.inStock))
  return fetch(`${BASE_URL}?${params}`).then((res) => handle<ProductPage>(res))
}

export function createProduct(input: ProductInput): Promise<Product> {
  return fetch(BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  }).then((res) => handle<Product>(res))
}

export function updateProduct(id: number, input: ProductInput): Promise<Product> {
  return fetch(`${BASE_URL}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  }).then((res) => handle<Product>(res))
}

export function deleteProduct(id: number): Promise<void> {
  return fetch(`${BASE_URL}/${id}`, { method: 'DELETE' }).then((res) => handle<void>(res))
}
