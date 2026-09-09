from tortoise import fields
from tortoise.models import Model


class OrderItem(Model):
    id = fields.IntField(pk=True)
    order = fields.ForeignKeyField("models.Order", related_name="items")
    product = fields.ForeignKeyField(
        "models.Product", related_name="order_items", null=True, on_delete=fields.SET_NULL
    )
    product_name = fields.CharField(max_length=200)
    unit_price = fields.DecimalField(max_digits=10, decimal_places=2)
    quantity = fields.IntField()

    class Meta:
        table = "order_items"
        ordering = ["id"]
