from tortoise import fields
from tortoise.models import Model


class CartItem(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="cart_items")
    product = fields.ForeignKeyField("models.Product", related_name="cart_items")
    quantity = fields.IntField(default=1)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "cart_items"
        unique_together = (("user", "product"),)
        ordering = ["created_at"]
