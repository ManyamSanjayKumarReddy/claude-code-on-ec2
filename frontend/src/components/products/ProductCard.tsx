import { useState } from 'react'
import { Pencil, PackageOpen, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import type { Product } from '@/types/product'

interface ProductCardProps {
  product: Product
  onEdit: () => void
  onDelete: () => void
}

export function ProductCard({ product, onEdit, onDelete }: ProductCardProps) {
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
      <CardFooter className="justify-end gap-2">
        <Button variant="outline" size="sm" onClick={onEdit}>
          <Pencil /> Edit
        </Button>
        <Button variant="destructive" size="sm" onClick={onDelete}>
          <Trash2 /> Delete
        </Button>
      </CardFooter>
    </Card>
  )
}
