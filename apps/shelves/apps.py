# apps/shelves/apps.py
from django.apps import AppConfig


class ShelvesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shelves'
    verbose_name = '棚管理'
