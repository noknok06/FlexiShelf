# apps/proposals/apps.py
from django.apps import AppConfig


class ProposalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.proposals'
    verbose_name = '提案管理'