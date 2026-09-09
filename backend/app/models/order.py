from tortoise import fields
from tortoise.models import Model


class Order(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="orders")
    status = fields.CharField(max_length=20, default="placed")
    recipient_name = fields.CharField(max_length=200)
    address_line1 = fields.CharField(max_length=255)
    address_line2 = fields.CharField(max_length=255, null=True)
    city = fields.CharField(max_length=100)
    state = fields.CharField(max_length=100)
    postal_code = fields.CharField(max_length=20)
    country = fields.CharField(max_length=100)
    shipping_method = fields.CharField(max_length=20)
    shipping_cost = fields.DecimalField(max_digits=10, decimal_places=2)
    subtotal = fields.DecimalField(max_digits=10, decimal_places=2)
    total = fields.DecimalField(max_digits=10, decimal_places=2)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "orders"
        ordering = ["-created_at"]
