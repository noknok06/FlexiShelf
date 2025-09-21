# apps/accounts/views.py
"""
ユーザー管理ビュー
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator


class ProfileView(TemplateView):
    """ユーザープロフィールビュー"""
    template_name = 'accounts/profile.html'
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


@login_required
def logout_view(request):
    """ログアウトビュー"""
    logout(request)
    messages.success(request, 'ログアウトしました。')
    return redirect('accounts:login')
