# apps/proposals/models.py（更新版）
"""
提案管理モデル（将来の実装用）
"""
from django.db import models
from apps.core.models import BaseModel


class Proposal(BaseModel):
    """提案（将来実装）"""
    title = models.CharField('提案タイトル', max_length=200)
    description = models.TextField('説明', blank=True)
    
    class Meta:
        verbose_name = '提案'
        verbose_name_plural = '提案'
        
    def __str__(self):
        return self.title