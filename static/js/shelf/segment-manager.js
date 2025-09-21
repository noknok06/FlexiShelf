/**
 * FlexiShelf - 段管理機能
 * 段の高さ調整、追加、削除などの機能を提供
 */

class SegmentManager {
    constructor() {
        this.segments = new Map();
        this.isResizing = false;
        this.resizeTarget = null;
        this.originalHeight = 0;
        this.startY = 0;
        
        this.init();
    }
    
    init() {
        this.loadSegments();
        this.setupEventListeners();
        this.setupResizeHandles();
    }
    
    loadSegments() {
        document.querySelectorAll('.segment').forEach(segmentEl => {
            const segmentData = {
                id: parseInt(segmentEl.dataset.segmentId),
                level: parseInt(segmentEl.dataset.level),
                height: parseFloat(segmentEl.dataset.height),
                element: segmentEl,
                placements: []
            };
            
            this.segments.set(segmentData.id, segmentData);
        });
    }
    
    setupEventListeners() {
        // 段高さスライダー
        document.querySelectorAll('.height-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                this.updateHeightPreview(e.target);
            });
            
            slider.addEventListener('change', (e) => {
                this.applyHeightChange(e.target);
            });
        });
        
        // 段高さ入力フィールド
        document.querySelectorAll('.height-input').forEach(input => {
            input.addEventListener('input', (e) => {
                this.syncHeightControls(e.target);
                this.updateHeightPreview(e.target);
            });
            
            input.addEventListener('change', (e) => {
                this.applyHeightChange(e.target);
            });
        });
        
        // キーボードショートカット
        document.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('height-input')) {
                if (e.key === 'Enter') {
                    e.target.blur();
                    this.applyHeightChange(e.target);
                }
            }
        });
    }
    
    setupResizeHandles() {
        document.querySelectorAll('.segment-resize-handle').forEach(handle => {
            handle.addEventListener('mousedown', (e) => {
                this.startResize(e, handle);
            });
        });
        
        document.addEventListener('mousemove', (e) => {
            if (this.isResizing) {
                this.updateResize(e);
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (this.isResizing) {
                this.endResize();
            }
        });
    }
    
    // 高さ調整のプレビュー
    updateHeightPreview(control) {
        const segmentId = parseInt(control.dataset.segmentId);
        const newHeight = parseFloat(control.value);
        
        if (isNaN(newHeight) || newHeight < 10) return;
        
        const segment = this.segments.get(segmentId);
        if (!segment) return;
        
        // 段の高さを一時的に更新
        segment.element.style.height = newHeight + 'px';
        segment.element.dataset.height = newHeight;
        
        // 段内の配置を再配置
        this.repositionPlacements(segment.element, newHeight);
        
        // 配置可能性をチェック
        this.validateHeightChange(segment, newHeight);
        
        // 他のコントロールと同期
        this.syncHeightControls(control, newHeight);
    }
    
    // 高さ変更の適用
    async applyHeightChange(control) {
        const segmentId = parseInt(control.dataset.segmentId);
        const newHeight = parseFloat(control.value);
        
        if (isNaN(newHeight) || newHeight < 10 || newHeight > 100) {
            this.showError('段の高さは10cm〜100cmの範囲で設定してください');
            this.revertHeightChange(segmentId);
            return;
        }
        
        const segment = this.segments.get(segmentId);
        if (!segment) return;
        
        // 配置可能性の最終チェック
        if (!this.canChangeHeight(segment, newHeight)) {
            this.revertHeightChange(segmentId);
            return;
        }
        
        try {
            // API呼び出し
            const response = await this.updateSegmentHeight(segmentId, newHeight);
            
            if (response.success) {
                // 成功時の処理
                segment.height = newHeight;
                this.updateSegmentData(segment, response.segment);
                this.updateShelfLayout();
                this.showSuccess(`段${segment.level}の高さを${newHeight}cmに変更しました`);
            } else {
                throw new Error(response.errors?.join(', ') || '高さの変更に失敗しました');
            }
        } catch (error) {
            console.error('Failed to update segment height:', error);
            this.showError('段の高さ変更に失敗しました: ' + error.message);
            this.revertHeightChange(segmentId);
        }
    }
    
    // 高さ変更のバリデーション
    canChangeHeight(segment, newHeight) {
        const placements = segment.element.querySelectorAll('.placement');
        
        for (let placement of placements) {
            const productHeight = parseFloat(placement.dataset.productHeight);
            if (productHeight > newHeight) {
                this.showError(
                    `配置されている商品「${placement.querySelector('.product-name').textContent}」の高さ（${productHeight}cm）が` +
                    `新しい段の高さ（${newHeight}cm）を超えています`
                );
                return false;
            }
        }
        
        return true;
    }
    
    validateHeightChange(segment, newHeight) {
        const placements = segment.element.querySelectorAll('.placement');
        let hasInvalidPlacements = false;
        
        placements.forEach(placement => {
            const productHeight = parseFloat(placement.dataset.productHeight);
            if (productHeight > newHeight) {
                placement.classList.add('error');
                hasInvalidPlacements = true;
            } else {
                placement.classList.remove('error');
            }
        });
        
        // 段の視覚的フィードバック
        if (hasInvalidPlacements) {
            segment.element.classList.add('drop-invalid');
        } else {
            segment.element.classList.remove('drop-invalid');
        }
        
        return !hasInvalidPlacements;
    }
    
    // 配置の再配置
    repositionPlacements(segmentEl, newHeight) {
        const placements = segmentEl.querySelectorAll('.placement');
        
        placements.forEach(placement => {
            const productHeight = parseFloat(placement.dataset.productHeight);
            const newTop = Math.max(2, newHeight - productHeight + 2);
            placement.style.top = newTop + 'px';
        });
    }
    
    // コントロールの同期
    syncHeightControls(changedControl, value = null) {
        const segmentId = changedControl.dataset.segmentId;
        const newValue = value || parseFloat(changedControl.value);
        
        document.querySelectorAll(`[data-segment-id="${segmentId}"]`).forEach(control => {
            if (control !== changedControl && 
                (control.classList.contains('height-slider') || control.classList.contains('height-input'))) {
                control.value = newValue;
            }
        });
    }
    
    // 高さ変更の取り消し
    revertHeightChange(segmentId) {
        const segment = this.segments.get(segmentId);
        if (!segment) return;
        
        const originalHeight = segment.height;
        
        // UI要素を元に戻す
        segment.element.style.height = originalHeight + 'px';
        segment.element.dataset.height = originalHeight;
        segment.element.classList.remove('drop-invalid');
        
        // コントロールを元に戻す
        document.querySelectorAll(`[data-segment-id="${segmentId}"]`).forEach(control => {
            if (control.classList.contains('height-slider') || control.classList.contains('height-input')) {
                control.value = originalHeight;
            }
        });
        
        // 配置を元に戻す
        this.repositionPlacements(segment.element, originalHeight);
        
        // エラー状態をクリア
        segment.element.querySelectorAll('.placement.error').forEach(placement => {
            placement.classList.remove('error');
        });
    }
    
    // マウスリサイズ機能
    startResize(e, handle) {
        e.preventDefault();
        
        this.isResizing = true;
        this.resizeTarget = handle;
        this.startY = e.clientY;
        
        const segmentId = parseInt(handle.dataset.segmentId);
        const segment = this.segments.get(segmentId);
        this.originalHeight = segment.height;
        
        document.body.style.cursor = 'ns-resize';
        document.body.style.userSelect = 'none';
        
        // 視覚的フィードバック
        handle.closest('.segment').classList.add('resizing');
    }
    
    updateResize(e) {
        if (!this.isResizing || !this.resizeTarget) return;
        
        const deltaY = e.clientY - this.startY;
        const newHeight = Math.max(10, Math.min(100, this.originalHeight + deltaY));
        
        const segmentId = parseInt(this.resizeTarget.dataset.segmentId);
        const segment = this.segments.get(segmentId);
        
        // プレビュー更新
        segment.element.style.height = newHeight + 'px';
        segment.element.dataset.height = newHeight;
        
        // 配置の再配置
        this.repositionPlacements(segment.element, newHeight);
        
        // バリデーション
        this.validateHeightChange(segment, newHeight);
        
        // コントロールの更新
        document.querySelectorAll(`[data-segment-id="${segmentId}"]`).forEach(control => {
            if (control.classList.contains('height-slider') || control.classList.contains('height-input')) {
                control.value = newHeight.toFixed(1);
            }
        });
    }
    
    endResize() {
        if (!this.isResizing) return;
        
        const segmentId = parseInt(this.resizeTarget.dataset.segmentId);
        const segment = this.segments.get(segmentId);
        const newHeight = parseFloat(segment.element.dataset.height);
        
        // 最終的な高さ変更を適用
        if (this.canChangeHeight(segment, newHeight)) {
            const control = document.querySelector(`[data-segment-id="${segmentId}"].height-input`);
            if (control) {
                this.applyHeightChange(control);
            }
        } else {
            this.revertHeightChange(segmentId);
        }
        
        // クリーンアップ
        this.isResizing = false;
        this.resizeTarget = null;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        
        document.querySelectorAll('.segment.resizing').forEach(seg => {
            seg.classList.remove('resizing');
        });
    }
    
    // 段データの更新
    updateSegmentData(segment, newData) {
        Object.assign(segment, newData);
        
        // DOM要素の更新
        segment.element.dataset.height = segment.height;
        if (newData.y_position !== undefined) {
            segment.element.style.top = newData.y_position + 'px';
        }
    }
    
    // 棚レイアウト全体の更新
    updateShelfLayout() {
        // 段の位置を再計算
        this.recalculateSegmentPositions();
        
        // 統計の更新
        if (window.placementEngine) {
            window.placementEngine.updateStatistics();
        }
        
        // レイアウト変更イベントの発火
        this.fireEvent('shelf:layout-changed');
    }
    
    // 段位置の再計算
    recalculateSegmentPositions() {
        const segments = Array.from(this.segments.values()).sort((a, b) => a.level - b.level);
        let currentY = 0;
        
        segments.forEach(segment => {
            segment.element.style.top = currentY + 'px';
            currentY += segment.height + 2; // 2pxは段間のマージン
        });
        
        // 棚全体の高さを更新
        const canvas = document.getElementById('shelf-canvas');
        if (canvas) {
            canvas.style.height = currentY + 'px';
        }
    }
    
    // 段の追加
    async addSegment(afterLevel = null) {
        try {
            const newLevel = afterLevel ? afterLevel + 1 : this.segments.size + 1;
            
            // 新しい段を作成（実装は複雑になるため基本的な枠組みのみ）
            this.showInfo('段の追加機能は開発中です');
            
        } catch (error) {
            this.showError('段の追加に失敗しました: ' + error.message);
        }
    }
    
    // 段の削除
    async removeSegment(segmentId) {
        const segment = this.segments.get(segmentId);
        if (!segment) return;
        
        // 配置チェック
        const placements = segment.element.querySelectorAll('.placement');
        if (placements.length > 0) {
            this.showError('商品が配置されている段は削除できません');
            return;
        }
        
        if (!confirm(`段${segment.level}を削除しますか？`)) return;
        
        try {
            // 削除機能は複雑になるため基本的な枠組みのみ
            this.showInfo('段の削除機能は開発中です');
            
        } catch (error) {
            this.showError('段の削除に失敗しました: ' + error.message);
        }
    }
    
    // 一括高さ適用
    async applyAllHeightChanges() {
        const changes = [];
        
        document.querySelectorAll('.height-input').forEach(input => {
            const segmentId = parseInt(input.dataset.segmentId);
            const newHeight = parseFloat(input.value);
            const segment = this.segments.get(segmentId);
            
            if (segment && Math.abs(segment.height - newHeight) > 0.1) {
                changes.push({ segmentId, newHeight, segment });
            }
        });
        
        if (changes.length === 0) {
            this.showInfo('変更された段はありません');
            return;
        }
        
        // バリデーション
        for (let change of changes) {
            if (!this.canChangeHeight(change.segment, change.newHeight)) {
                return; // エラーは canChangeHeight 内で表示される
            }
        }
        
        try {
            // 順次適用
            for (let change of changes) {
                await this.updateSegmentHeight(change.segmentId, change.newHeight);
                change.segment.height = change.newHeight;
            }
            
            this.updateShelfLayout();
            this.showSuccess(`${changes.length}段の高さを一括更新しました`);
            
        } catch (error) {
            this.showError('一括更新に失敗しました: ' + error.message);
            
            // 失敗時は全て元に戻す
            changes.forEach(change => {
                this.revertHeightChange(change.segmentId);
            });
        }
    }
    
    // API呼び出し
    async updateSegmentHeight(segmentId, height) {
        const formData = new FormData();
        formData.append('height', height);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());
        
        const response = await fetch(`/api/segment/${segmentId}/height/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        return await response.json();
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    // プリセット高さの適用
    applyPresetHeights(preset) {
        const presets = {
            uniform: { height: 30, description: '全段30cm（標準）' },
            tall: { height: 40, description: '全段40cm（高さのある商品用）' },
            mixed: { heights: [25, 30, 35, 40], description: '段階的（下から25,30,35,40cm）' },
            grocery: { heights: [20, 25, 30, 35], description: '食品店向け' }
        };
        
        const config = presets[preset];
        if (!config) return;
        
        if (config.height) {
            // 均一高さ
            document.querySelectorAll('.height-input').forEach(input => {
                input.value = config.height;
                this.updateHeightPreview(input);
            });
        } else if (config.heights) {
            // 個別高さ
            const inputs = document.querySelectorAll('.height-input');
            inputs.forEach((input, index) => {
                if (index < config.heights.length) {
                    input.value = config.heights[index];
                    this.updateHeightPreview(input);
                }
            });
        }
        
        this.showInfo(`プリセット「${config.description}」を適用しました`);
    }
    
    // 最適化機能
    optimizeHeights() {
        // 配置されている商品の高さに基づいて最適な段高さを計算
        const segments = Array.from(this.segments.values());
        
        segments.forEach(segment => {
            const placements = segment.element.querySelectorAll('.placement');
            if (placements.length === 0) return;
            
            let maxProductHeight = 0;
            placements.forEach(placement => {
                const productHeight = parseFloat(placement.dataset.productHeight);
                maxProductHeight = Math.max(maxProductHeight, productHeight);
            });
            
            // 商品高さ + 余裕（5cm）
            const optimalHeight = Math.max(20, maxProductHeight + 5);
            
            const input = document.querySelector(`[data-segment-id="${segment.id}"].height-input`);
            if (input) {
                input.value = optimalHeight;
                this.updateHeightPreview(input);
            }
        });
        
        this.showInfo('商品高さに基づいて段高さを最適化しました');
    }
    
    // ユーティリティ
    fireEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showInfo(message) {
        this.showMessage(message, 'info');
    }
    
    showMessage(message, type) {
        if (typeof FlexiShelf !== 'undefined' && FlexiShelf.showToast) {
            FlexiShelf.showToast(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    // 段情報の取得
    getSegmentInfo(segmentId) {
        return this.segments.get(segmentId);
    }
    
    getAllSegments() {
        return Array.from(this.segments.values()).sort((a, b) => a.level - b.level);
    }
    
    // 段の統計情報
    getSegmentStatistics() {
        const segments = this.getAllSegments();
        
        return {
            totalSegments: segments.length,
            totalHeight: segments.reduce((sum, seg) => sum + seg.height, 0),
            averageHeight: segments.length > 0 ? segments.reduce((sum, seg) => sum + seg.height, 0) / segments.length : 0,
            heightRange: {
                min: Math.min(...segments.map(seg => seg.height)),
                max: Math.max(...segments.map(seg => seg.height))
            }
        };
    }
}

// グローバルインスタンス
window.segmentManager = new SegmentManager();

// 公開API
window.SegmentAPI = {
    applyHeightChanges: () => window.segmentManager.applyAllHeightChanges(),
    addSegment: (afterLevel) => window.segmentManager.addSegment(afterLevel),
    removeSegment: (segmentId) => window.segmentManager.removeSegment(segmentId),
    applyPreset: (preset) => window.segmentManager.applyPresetHeights(preset),
    optimize: () => window.segmentManager.optimizeHeights(),
    getStatistics: () => window.segmentManager.getSegmentStatistics()
};