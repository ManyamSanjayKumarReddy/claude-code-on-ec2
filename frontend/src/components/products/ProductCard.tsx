import { Pencil, PackageOpen, Trash2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
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

  return (
    <Card className="flex flex-col overflow-hidden">
      {product.image_url ? (
        <img
          src={product.image_url}
          alt={product.name}
          className="aspect-square w-full object-cover"
          loading="lazy"
          onError={(e) => {
            e.currentTarget.style.display = 'none'
          }}
        />
      ) : (
        <div className="flex aspect-square w-full items-center justify-center bg-muted">
          <PackageOpen className="size-10 text-muted-foreground" />
        </div>
      )}
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{product.name}</CardTitle>
          <Badge variant={outOfStock ? 'destructive' : 'secondary'} className="shrink-0">
            {outOfStock ? 'Out of stock' : `${product.stock_quantity} in stock`}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        {product.description && (
          <p className="line-clamp-3 text-sm text-muted-foreground">{product.description}</p>
        )}
        <p className="mt-3 text-xl font-semibold">${product.price}</p>
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
