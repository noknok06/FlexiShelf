"""
ユーザー管理モデル
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """カスタムユーザーモデル"""
    
    ROLE_CHOICES = [
        ('admin', '管理者'),
        ('manager', 'マネージャー'),
        ('staff', 'スタッフ'),
    ]
    
    email = models.EmailField('メールアドレス', unique=True)
    role = models.CharField('役職', max_length=20, choices=ROLE_CHOICES, default='staff')
    department = models.CharField('部署', max_length=100, blank=True)
    phone = models.CharField('電話番号', max_length=20, blank=True)
    is_email_verified = models.BooleanField('メール認証済み', default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'
        db_table = 'auth_user'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """フルネームを返す"""
        return f"{self.last_name} {self.first_name}".strip()
    
    @property
    def is_manager(self):
        """マネージャー権限を持つか"""
        return self.role in ['admin', 'manager']
    
    @property
    def is_admin(self):
        """管理者権限を持つか"""
        return self.role == 'admin'