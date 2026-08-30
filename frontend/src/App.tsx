import { useEffect, useState } from 'react'
import { PackageOpen, Plus } from 'lucide-react'

import { createProduct, deleteProduct, listProducts, updateProduct } from '@/api/products'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ProductCard } from '@/components/products/ProductCard'
import { ProductForm } from '@/components/products/ProductForm'
import type { Product, ProductInput } from '@/types/product'

function App() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [formOpen, setFormOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null)

  useEffect(() => {
    refresh()
  }, [])

  async function refresh() {
    setLoading(true)
    setError(null)
    try {
      setProducts(await listProducts())
    } catch {
      setError('Could not load products. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  function openAddForm() {
    setEditingProduct(null)
    setFormOpen(true)
  }

  function openEditForm(product: Product) {
    setEditingProduct(product)
    setFormOpen(true)
  }

  async function handleSubmit(input: ProductInput) {
    if (editingProduct) {
      await updateProduct(editingProduct.id, input)
    } else {
      await createProduct(input)
    }
    setFormOpen(false)
    await refresh()
  }

  async function handleConfirmDelete() {
    if (!deletingProduct) return
    await deleteProduct(deletingProduct.id)
    setDeletingProduct(null)
    await refresh()
  }

  return (
    <main className="mx-auto min-h-svh max-w-5xl px-6 py-10">
      <header className="mb-8 flex items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-semibold">My Store</h1>
          <p className="text-sm text-muted-foreground">Manage your product catalog</p>
        </div>
        <Button onClick={openAddForm}>
          <Plus /> Add product
        </Button>
      </header>

      {loading && <p className="text-sm text-muted-foreground">Loading products...</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {!loading && !error && products.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-16 text-center">
          <PackageOpen className="size-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No products yet. Add your first one to get started.</p>
          <Button onClick={openAddForm}>
            <Plus /> Add product
          </Button>
        </div>
      )}

      {!loading && !error && products.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onEdit={() => openEditForm(product)}
              onDelete={() => setDeletingProduct(product)}
            />
          ))}
        </div>
      )}

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{editingProduct ? 'Edit product' : 'Add product'}</DialogTitle>
          </DialogHeader>
          <ProductForm
            initial={editingProduct}
            onSubmit={handleSubmit}
            onCancel={() => setFormOpen(false)}
          />
        </DialogContent>
      </Dialog>

      <AlertDialog open={deletingProduct !== null} onOpenChange={(open) => !open && setDeletingProduct(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete "{deletingProduct?.name}"?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently remove the product from your catalog.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  )
}

export default App
