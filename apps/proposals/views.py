# apps/proposals/views.py
"""
提案管理ビュー（基本実装）
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class ProposalListView(ListView):
    """提案一覧ビュー（仮実装）"""
    template_name = 'proposals/list.html'
    context_object_name = 'proposals'
    
    def get_queryset(self):
        # 現在は空のクエリセット
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = '提案機能は今後のバージョンで実装予定です。'
        return context
