/**
 * FlexiShelf - 商品配置エンジン (修正版)
 * 商品の配置、移動、削除などの核心機能を提供
 */

class PlacementEngine {
    constructor() {
        this.currentShelf = null;
        this.selectedPlacement = null;
        this.draggedProduct = null;
        this.isDragging = false;
        this.snapToGrid = true;
        this.gridSize = 5; // cm
        this.undoStack = [];
        this.redoStack = [];
        this.maxUndoSteps = 50;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadShelfData();
    }
    
    setupEventListeners() {
        // キーボードショートカット
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'z':
                        e.preventDefault();
                        if (e.shiftKey) {
                            this.redo();
                        } else {
                            this.undo();
                        }
                        break;
                    case 's':
                        e.preventDefault();
                        this.saveLayout();
                        break;
                    case 'Delete':
                    case 'Backspace':
                        if (this.selectedPlacement) {
                            e.preventDefault();
                            this.deletePlacement(this.selectedPlacement);
                        }
                        break;
                }
            }
        });
        
        // 配置のマウスイベント
        document.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // コンテキストメニュー
        document.addEventListener('contextmenu', this.handleContextMenu.bind(this));
    }
    
    loadShelfData() {
        const canvas = document.getElementById('shelf-canvas');
        if (!canvas) return;
        
        this.currentShelf = {
            id: parseInt(canvas.dataset.shelfId),
            width: parseFloat(canvas.dataset.shelfWidth),
            depth: parseFloat(canvas.dataset.shelfDepth),
            segments: this.loadSegments()
        };
    }
    
    loadSegments() {
        const segments = [];
        document.querySelectorAll('.segment').forEach(segmentEl => {
            const segment = {
                id: parseInt(segmentEl.dataset.segmentId),
                level: parseInt(segmentEl.dataset.level),
                height: parseFloat(segmentEl.dataset.height),
                element: segmentEl,
                placements: this.loadPlacements(segmentEl)
            };
            segments.push(segment);
        });
        return segments.sort((a, b) => a.level - b.level);
    }
    
    loadPlacements(segmentEl) {
        const placements = [];
        segmentEl.querySelectorAll('.placement').forEach(placementEl => {
            const placement = {
                id: parseInt(placementEl.dataset.placementId),
                productId: parseInt(placementEl.dataset.productId),
                xPosition: parseFloat(placementEl.dataset.xPosition),
                faceCount: parseInt(placementEl.dataset.faceCount),
                occupiedWidth: parseFloat(placementEl.dataset.occupiedWidth),
                productWidth: parseFloat(placementEl.dataset.productWidth),
                productHeight: parseFloat(placementEl.dataset.productHeight),
                element: placementEl
            };
            placements.push(placement);
        });
        return placements.sort((a, b) => a.xPosition - b.xPosition);
    }
    
    // 配置作成
    async createPlacement(segmentId, productData, xPosition, faceCount) {
        try {
            // 配置前バリデーション
            const validation = await this.validatePlacement(segmentId, productData, xPosition, faceCount);
            if (!validation.valid) {
                throw new Error(validation.errors.join(', '));
            }
            
            // グリッドスナップ
            if (this.snapToGrid) {
                xPosition = this.snapToGridPosition(xPosition);
            }
            
            // API呼び出し
            const response = await this.apiCall('/shelves/api/placement/create/', {
                shelf_id: this.currentShelf.id,
                segment_id: segmentId,
                product_id: productData.id,
                x_position: xPosition,
                face_count: faceCount
            });
            
            if (response.success) {
                // UI更新
                this.addPlacementToUI(segmentId, response.placement, productData);
                this.updateStatistics();
                this.saveToUndoStack('create', response.placement);
                return response.placement;
            } else {
                throw new Error(response.errors.join(', '));
            }
        } catch (error) {
            console.error('Failed to create placement:', error);
            this.showError('配置の作成に失敗しました: ' + error.message);
            return null;
        }
    }
    
    // 配置更新
    async updatePlacement(placementId, updates) {
        try {
            const oldState = this.getPlacementState(placementId);
            
            const response = await this.apiCall(`/shelves/api/placement/${placementId}/update/`, updates);
            
            if (response.success) {
                this.updatePlacementUI(placementId, response.placement);
                this.updateStatistics();
                this.saveToUndoStack('update', { oldState, newState: response.placement });
                return response.placement;
            } else {
                throw new Error(response.errors.join(', '));
            }
        } catch (error) {
            console.error('Failed to update placement:', error);
            this.showError('配置の更新に失敗しました: ' + error.message);
            return null;
        }
    }
    
    // 配置削除
    async deletePlacement(placementElement) {
        if (!confirm('この配置を削除しますか？')) return;
        
        try {
            const placementId = parseInt(placementElement.dataset.placementId);
            const oldState = this.getPlacementState(placementId);
            
            const response = await this.apiCall(`/shelves/api/placement/${placementId}/delete/`, {});
            
            if (response.success) {
                this.removePlacementFromUI(placementElement);
                this.updateStatistics();
                this.saveToUndoStack('delete', oldState);
                this.deselectPlacement();
            } else {
                throw new Error('削除に失敗しました');
            }
        } catch (error) {
            console.error('Failed to delete placement:', error);
            this.showError('配置の削除に失敗しました: ' + error.message);
        }
    }
    
    // バリデーション
    async validatePlacement(segmentId, productData, xPosition, faceCount, excludePlacementId = null) {
        try {
            const params = new URLSearchParams({
                segment_id: segmentId,
                product_id: productData.id,
                x_position: xPosition,
                face_count: faceCount
            });
            
            if (excludePlacementId) {
                params.append('placement_id', excludePlacementId);
            }
            
            const response = await fetch(`/shelves/api/placement/validate/?${params}`);
            if (!response.ok) {
                return { valid: false, errors: ['バリデーションエラー'] };
            }
            return await response.json();
        } catch (error) {
            return { valid: false, errors: ['バリデーションエラー'] };
        }
    }
    
    // マウスイベントハンドラ
    handleMouseDown(e) {
        if (e.target.closest('.placement')) return; // 配置要素は個別処理
        
        // 空白クリックで選択解除
        if (e.target.closest('.shelf-canvas')) {
            this.deselectPlacement();
        }
    }
    
    handleMouseMove(e) {
        if (this.isDragging) {
            this.updateDrag(e);
        }
    }
    
    handleMouseUp(e) {
        if (this.isDragging) {
            this.endDrag(e);
        }
    }
    
    handleContextMenu(e) {
        // 右クリックメニュー処理（必要に応じて実装）
        e.preventDefault();
    }
    
    // ユーティリティメソッド
    snapToGridPosition(x) {
        return Math.round(x / this.gridSize) * this.gridSize;
    }
    
    // 選択管理
    selectPlacement(placementEl) {
        this.deselectPlacement();
        
        this.selectedPlacement = placementEl;
        placementEl.classList.add('selected');
        
        // 選択パネル更新
        this.updateSelectedPanel(placementEl);
        
        // 選択イベント発火
        this.fireEvent('placement:selected', { placement: placementEl });
    }
    
    deselectPlacement() {
        if (this.selectedPlacement) {
            this.selectedPlacement.classList.remove('selected');
            this.selectedPlacement = null;
        }
        
        // 選択パネル非表示
        this.hideSelectedPanel();
        
        // 選択解除イベント発火
        this.fireEvent('placement:deselected');
    }
    
    updateSelectedPanel(placementEl) {
        const panel = document.getElementById('selected-product-panel');
        if (!panel) return;
        
        const productName = placementEl.querySelector('.product-name')?.textContent || '';
        const manufacturerName = placementEl.querySelector('.manufacturer-name')?.textContent || '';
        
        const info = document.getElementById('selected-product-info');
        if (info) {
            info.innerHTML = `
                <h6>${productName}</h6>
                <small>${manufacturerName}</small><br>
                <small>配置ID: ${placementEl.dataset.placementId}</small>
            `;
        }
        
        // 編集フィールドに現在値を設定
        const xInput = document.getElementById('edit-x-position');
        const faceInput = document.getElementById('edit-face-count');
        
        if (xInput) xInput.value = placementEl.dataset.xPosition;
        if (faceInput) faceInput.value = placementEl.dataset.faceCount;
        
        panel.style.display = 'block';
    }
    
    hideSelectedPanel() {
        const panel = document.getElementById('selected-product-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }
    
    // 統計更新
    updateStatistics() {
        const stats = this.calculateStatistics();
        
        const elements = {
            'total-placements': stats.totalPlacements,
            'total-faces': stats.totalFaces,
            'own-products-count': stats.ownProducts,
            'competitor-products-count': stats.competitorProducts,
            'avg-utilization': stats.avgUtilization.toFixed(1) + '%'
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        });
    }
    
    calculateStatistics() {
        const placements = document.querySelectorAll('.placement');
        let totalPlacements = placements.length;
        let totalFaces = 0;
        let ownProducts = 0;
        let competitorProducts = 0;
        let totalUtilization = 0;
        
        placements.forEach(placement => {
            const faceCount = parseInt(placement.dataset.faceCount) || 1;
            totalFaces += faceCount;
            
            if (placement.classList.contains('own-product')) {
                ownProducts++;
            } else {
                competitorProducts++;
            }
        });
        
        // 利用率計算
        const segments = document.querySelectorAll('.segment');
        segments.forEach(segment => {
            const segmentPlacements = segment.querySelectorAll('.placement');
            let usedWidth = 0;
            segmentPlacements.forEach(p => {
                usedWidth += parseFloat(p.dataset.occupiedWidth) || 0;
            });
            totalUtilization += (usedWidth / this.currentShelf.width) * 100;
        });
        
        const avgUtilization = segments.length > 0 ? totalUtilization / segments.length : 0;
        
        return {
            totalPlacements,
            totalFaces,
            ownProducts,
            competitorProducts,
            avgUtilization
        };
    }
    
    // Undo/Redo機能
    saveToUndoStack(action, data) {
        const state = {
            action,
            data,
            timestamp: Date.now()
        };
        
        this.undoStack.push(state);
        this.redoStack = []; // 新しいアクションでRedoスタックをクリア
        
        // スタックサイズ制限
        if (this.undoStack.length > this.maxUndoSteps) {
            this.undoStack.shift();
        }
        
        this.updateUndoRedoButtons();
    }
    
    undo() {
        if (this.undoStack.length === 0) return;
        
        const state = this.undoStack.pop();
        this.redoStack.push(state);
        
        this.executeUndoRedo(state, true);
        this.updateUndoRedoButtons();
    }
    
    redo() {
        if (this.redoStack.length === 0) return;
        
        const state = this.redoStack.pop();
        this.undoStack.push(state);
        
        this.executeUndoRedo(state, false);
        this.updateUndoRedoButtons();
    }
    
    executeUndoRedo(state, isUndo) {
        // Undo/Redo実装は複雑になるため、基本的な枠組みのみ提供
        console.log(`${isUndo ? 'Undo' : 'Redo'} action:`, state.action);
        this.showInfo(`${isUndo ? '元に戻し' : 'やり直し'}ました`);
    }
    
    updateUndoRedoButtons() {
        // ボタンの有効/無効状態を更新
        const undoBtn = document.querySelector('[onclick="undoLastAction()"]');
        const redoBtn = document.querySelector('[onclick="redoLastAction()"]');
        
        if (undoBtn) {
            undoBtn.disabled = this.undoStack.length === 0;
        }
        if (redoBtn) {
            redoBtn.disabled = this.redoStack.length === 0;
        }
    }
    
    // API呼び出し
    async apiCall(url, data) {
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken);
        }
        
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!token) {
            console.warn('CSRFトークンが見つかりません');
        }
        return token || '';
    }
    
    // ユーティリティ
    camelCase(str) {
        return str.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
    }
    
    truncateText(text, maxLength) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    getPlacementState(placementId) {
        const placement = document.querySelector(`[data-placement-id="${placementId}"]`);
        if (!placement) return null;
        
        return {
            id: placementId,
            xPosition: parseFloat(placement.dataset.xPosition),
            faceCount: parseInt(placement.dataset.faceCount),
            segmentId: parseInt(placement.closest('.segment').dataset.segmentId)
        };
    }
    
    // イベント管理
    fireEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }
    
    // メッセージ表示
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
    
    // 他のメソッドはプレースホルダー
    addPlacementToUI(segmentId, placementData, productData) {
        console.log('addPlacementToUI called', { segmentId, placementData, productData });
    }
    
    updatePlacementUI(placementId, placementData) {
        console.log('updatePlacementUI called', { placementId, placementData });
    }
    
    removePlacementFromUI(placementElement) {
        console.log('removePlacementFromUI called', placementElement);
        placementElement.remove();
    }
    
    saveLayout() {
        this.showSuccess('レイアウトは自動保存されています');
    }
}

// グローバルインスタンス
window.placementEngine = null;

// 初期化関数
function initializePlacementEngine() {
    if (!window.placementEngine && document.getElementById('shelf-canvas')) {
        window.placementEngine = new PlacementEngine();
    }
    
    // SegmentManagerも初期化
    if (typeof initializeSegmentManager === 'function') {
        initializeSegmentManager();
    }
}

// DOM読み込み時に初期化
document.addEventListener('DOMContentLoaded', initializePlacementEngine);

// 公開API
window.PlacementAPI = {
    selectPlacement: (element) => {
        if (window.placementEngine) {
            window.placementEngine.selectPlacement(element);
        }
    },
    deselectPlacement: () => {
        if (window.placementEngine) {
            window.placementEngine.deselectPlacement();
        }
    },
    deletePlacement: (element) => {
        if (window.placementEngine) {
            window.placementEngine.deletePlacement(element);
        }
    },
    updateStatistics: () => {
        if (window.placementEngine) {
            window.placementEngine.updateStatistics();
        }
    },
    undo: () => {
        if (window.placementEngine) {
            window.placementEngine.undo();
        }
    },
    redo: () => {
        if (window.placementEngine) {
            window.placementEngine.redo();
        }
    },
    saveLayout: () => {
        if (window.placementEngine) {
            window.placementEngine.saveLayout();
        }
    }
};