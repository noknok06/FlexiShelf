/**
 * FlexiShelf - 基本JavaScript機能
 */

// DOM読み込み完了時の初期化
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap tooltipの初期化
    initializeTooltips();
    
    // 自動非表示メッセージの設定
    setupAutoHideMessages();
    
    // 削除確認ダイアログの設定
    setupDeleteConfirmation();
    
    // フォームバリデーションの強化
    setupFormValidation();
});

/**
 * Bootstrap Tooltipの初期化
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * メッセージの自動非表示設定
 */
function setupAutoHideMessages() {
    const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
    alerts.forEach(alert => {
        // 成功・情報メッセージは5秒後に自動非表示
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
}

/**
 * 削除確認ダイアログの設定
 */
function setupDeleteConfirmation() {
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirmDelete || '本当に削除しますか？';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * フォームバリデーションの強化
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

/**
 * 共通ユーティリティ関数
 */
const FlexiShelf = {
    
    /**
     * CSRFトークンを取得
     */
    getCSRFToken: function() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    },
    
    /**
     * Ajax POST リクエスト
     */
    post: function(url, data = {}) {
        const formData = new FormData();
        Object.keys(data).forEach(key => {
            formData.append(key, data[key]);
        });
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());
        
        return fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
    },
    
    /**
     * ローディングスピナーの表示/非表示
     */
    showLoading: function(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>';
            element.disabled = true;
        }
    },
    
    hideLoading: function(element, originalText = 'OK') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.innerHTML = originalText;
            element.disabled = false;
        }
    },
    
    /**
     * トーストメッセージの表示
     */
    showToast: function(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container') || this.createToastContainer();
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-bg-${type} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        
        // トースト非表示後に要素を削除
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    },
    
    /**
     * トーストコンテナの作成
     */
    createToastContainer: function() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    },
    
    /**
     * 数値フォーマット（日本語形式）
     */
    formatNumber: function(num) {
        return new Intl.NumberFormat('ja-JP').format(num);
    },
    
    /**
     * 通貨フォーマット
     */
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('ja-JP', {
            style: 'currency',
            currency: 'JPY'
        }).format(amount);
    },
    
    /**
     * 日付フォーマット
     */
    formatDate: function(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        };
        return new Intl.DateTimeFormat('ja-JP', {...defaultOptions, ...options}).format(new Date(date));
    }
};

// グローバルに公開
window.FlexiShelf = FlexiShelf;