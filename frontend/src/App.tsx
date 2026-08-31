import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, PackageOpen, Plus } from 'lucide-react'

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
import { ThemeToggle } from '@/components/ThemeToggle'
import type { Product, ProductInput } from '@/types/product'

const PAGE_SIZE = 20

function App() {
  const [products, setProducts] = useState<Product[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [formOpen, setFormOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null)

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  useEffect(() => {
    refresh(page)
  }, [page])

  async function refresh(targetPage = page) {
    setLoading(true)
    setError(null)
    try {
      const result = await listProducts(targetPage, PAGE_SIZE)
      setProducts(result.items)
      setTotal(result.total)
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
    <div className="min-h-svh bg-gradient-to-b from-background via-background to-muted/40">
      <main className="mx-auto max-w-5xl px-6 py-10">
        <header className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="font-heading bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-2xl font-semibold text-transparent">
              My Store
            </h1>
            <p className="text-sm text-muted-foreground">Manage your product catalog</p>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button
              onClick={openAddForm}
              className="bg-gradient-to-r from-primary to-primary/80 hover:opacity-90"
            >
              <Plus /> Add product
            </Button>
          </div>
        </header>

      {loading && <p className="text-sm text-muted-foreground">Loading products...</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {!loading && !error && products.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-16 text-center">
          <PackageOpen className="size-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No products yet. Add your first one to get started.</p>
          <Button onClick={openAddForm} className="bg-gradient-to-r from-primary to-primary/80 hover:opacity-90">
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

      {!loading && !error && total > 0 && (
        <div className="mt-6 flex items-center justify-between gap-4">
          <p className="text-sm text-muted-foreground">
            Page {page} of {totalPages} &middot; {total} product{total === 1 ? '' : 's'}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              <ChevronLeft /> Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next <ChevronRight />
            </Button>
          </div>
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
    </div>
  )
}

export default App
