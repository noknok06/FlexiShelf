# apps/accounts/views.py
"""
ユーザー管理ビュー
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, FormView, UpdateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import User


class CustomLoginView(LoginView):
    """カスタムログインビュー"""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('home')
    
    def form_valid(self, form):
        messages.success(self.request, f'ようこそ、{form.get_user().get_full_name() or form.get_user().username}さん！')
        return super().form_valid(form)


class RegisterView(FormView):
    """ユーザー登録ビュー"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        # 既にログイン済みの場合はホームにリダイレクト
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request, 
            f'{user.get_full_name()}さん、FlexiShelfへようこそ！アカウントが作成されました。'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '入力内容に誤りがあります。確認してください。')
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    """ユーザープロフィールビュー"""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    """プロフィール編集ビュー"""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'プロフィールを更新しました。')
        return super().form_valid(form)


@login_required
def logout_view(request):
    """ログアウトビュー"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'{user_name}さん、ログアウトしました。')
    return redirect('accounts:login')