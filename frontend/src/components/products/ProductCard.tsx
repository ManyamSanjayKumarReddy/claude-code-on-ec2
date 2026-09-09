import { useState } from 'react'
import { Pencil, PackageOpen, ShoppingCart, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import type { Product } from '@/types/product'

interface ProductCardProps {
  product: Product
  onEdit: () => void
  onDelete: () => void
  onAddToCart: () => void
}

export function ProductCard({ product, onEdit, onDelete, onAddToCart }: ProductCardProps) {
  const outOfStock = product.stock_quantity === 0
  const [imageFailed, setImageFailed] = useState(false)
  const showImage = product.image_url && !imageFailed

  return (
    <Card className="flex flex-col overflow-hidden transition-all hover:-translate-y-0.5 hover:shadow-md">
      {showImage ? (
        <img
          src={product.image_url!}
          alt={product.name}
          className="aspect-square w-full object-cover"
          loading="lazy"
          onError={() => setImageFailed(true)}
        />
      ) : (
        <div className="flex aspect-square w-full flex-col items-center justify-center gap-1 border-b bg-muted">
          <PackageOpen className="size-8 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">No image</span>
        </div>
      )}
      <CardHeader>
        <CardTitle className="line-clamp-2 text-sm">{product.name}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        {product.description && (
          <p className="line-clamp-2 text-xs text-muted-foreground">{product.description}</p>
        )}
        <div className="mt-2 flex items-center justify-between">
          <p className="text-lg font-semibold text-primary">${product.price}</p>
          <span
            className={`text-xs font-medium ${outOfStock ? 'text-destructive' : 'text-muted-foreground'}`}
          >
            {outOfStock ? 'Out of stock' : `${product.stock_quantity} in stock`}
          </span>
        </div>
      </CardContent>
      <CardFooter className="justify-between gap-2">
        <Button size="sm" onClick={onAddToCart} disabled={outOfStock}>
          <ShoppingCart /> Add to cart
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" size="icon-sm" onClick={onEdit} aria-label="Edit product">
            <Pencil />
          </Button>
          <Button variant="destructive" size="icon-sm" onClick={onDelete} aria-label="Delete product">
            <Trash2 />
          </Button>
        </div>
      </CardFooter>
    </Card>
  )
}
