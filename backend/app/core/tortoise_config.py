from app.core.config import settings

TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": ["app.models.product", "aerich.models"],
            "default_connection": "default",
        }
    },
}
