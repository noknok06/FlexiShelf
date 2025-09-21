"""
共通抽象モデル
"""
from django.db import models
from django.contrib.auth import get_user_model


class TimestampMixin(models.Model):
    """タイムスタンプ情報を持つ抽象モデル"""
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        abstract = True


class UserTrackableMixin(models.Model):
    """ユーザー追跡情報を持つ抽象モデル"""
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='作成者'
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='更新者'
    )

    class Meta:
        abstract = True


class BaseModel(TimestampMixin, UserTrackableMixin):
    """基底モデル"""
    is_active = models.BooleanField('有効', default=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """ソフトデリート"""
        self.is_active = False
        self.save()

    def hard_delete(self, *args, **kwargs):
        """物理削除"""
        super().delete(*args, **kwargs)