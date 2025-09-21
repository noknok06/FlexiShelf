# apps/core/mixins.py
"""
共通ミックスイン
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect


class FlexiShelfLoginRequiredMixin(LoginRequiredMixin):
    """FlexiShelf専用ログイン必須ミックスイン"""
    login_url = '/accounts/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, 'ログインが必要です。')
        return super().dispatch(request, *args, **kwargs)


class UserTrackingMixin:
    """ユーザー追跡ミックスイン"""
    
    def form_valid(self, form):
        if hasattr(form.instance, 'created_by') and not form.instance.pk:
            form.instance.created_by = self.request.user
        
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
            
        return super().form_valid(form)


class MessageMixin:
    """メッセージ表示ミックスイン"""
    success_message = None
    error_message = None
    
    def form_valid(self, form):
        if self.success_message:
            messages.success(self.request, self.success_message)
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.error_message:
            messages.error(self.request, self.error_message)
        return super().form_invalid(form)