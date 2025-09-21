# apps/accounts/admin.py
"""
ユーザー管理の管理画面設定
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """カスタムユーザー管理画面"""
    
    # リスト表示設定
    list_display = (
        'username', 'email', 'full_name_display', 'role_display', 
        'department', 'is_active', 'is_staff', 'date_joined'
    )
    list_filter = (
        'role', 'is_active', 'is_staff', 'is_superuser', 
        'department', 'date_joined'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'department')
    ordering = ('-date_joined',)
    
    # 詳細表示設定
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('個人情報', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('組織情報', {
            'fields': ('role', 'department')
        }),
        ('権限', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 
                'is_email_verified', 'groups', 'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('重要な日付', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # 新規作成時の設定
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'password1', 'password2', 'role', 'department'
            ),
        }),
    )
    
    # カスタム表示メソッド
    def full_name_display(self, obj):
        """フルネーム表示"""
        full_name = obj.get_full_name()
        if full_name:
            return full_name
        return '-'
    full_name_display.short_description = '氏名'
    
    def role_display(self, obj):
        """役職表示（色付き）"""
        colors = {
            'admin': 'red',
            'manager': 'orange', 
            'staff': 'green'
        }
        color = colors.get(obj.role, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_display.short_description = '役職'
    
    # アクション
    actions = ['make_active', 'make_inactive', 'verify_email']
    
    def make_active(self, request, queryset):
        """ユーザーを有効化"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated}人のユーザーを有効化しました。')
    make_active.short_description = '選択したユーザーを有効化'
    
    def make_inactive(self, request, queryset):
        """ユーザーを無効化"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated}人のユーザーを無効化しました。')
    make_inactive.short_description = '選択したユーザーを無効化'
    
    def verify_email(self, request, queryset):
        """メールアドレスを認証済みにする"""
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'{updated}人のメールアドレスを認証済みにしました。')
    verify_email.short_description = '選択したユーザーのメールアドレスを認証済みにする'