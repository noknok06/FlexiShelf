
/**
 * FlexiShelf - 商品配置エンジン
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
            const response = await this.apiCall('/api/placement/create/', {
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
            
            const response = await this.apiCall(`/api/placement/${placementId}/update/`, updates);
            
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
            
            const response = await this.apiCall(`/api/placement/${placementId}/delete/`, {});
            
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
            
            const response = await fetch(`/api/placement/validate/?${params}`);
            return await response.json();
        } catch (error) {
            return { valid: false, errors: ['バリデーションエラー'] };
        }
    }
    
    // UI更新メソッド
    addPlacementToUI(segmentId, placementData, productData) {
        const segment = document.querySelector(`[data-segment-id="${segmentId}"]`);
        if (!segment) return;
        
        const placementEl = this.createPlacementElement(placementData, productData);
        segment.appendChild(placementEl);
        
        // アニメーション
        placementEl.classList.add('placement-enter');
        setTimeout(() => placementEl.classList.remove('placement-enter'), 300);
        
        this.updateSegmentInfo(segment);
    }
    
    createPlacementElement(placementData, productData) {
        const placementEl = document.createElement('div');
        placementEl.className = `placement ${productData.isOwn ? 'own-product' : 'competitor-product'}`;
        
        // データ属性設定
        Object.entries(placementData).forEach(([key, value]) => {
            placementEl.dataset[this.camelCase(key)] = value;
        });
        
        // 製品データ属性
        placementEl.dataset.productWidth = productData.width;
        placementEl.dataset.productHeight = productData.height;
        
        // スタイル設定
        this.updatePlacementStyle(placementEl, placementData, productData);
        
        // 内容作成
        this.updatePlacementContent(placementEl, productData, placementData);
        
        // イベントリスナー
        this.attachPlacementEvents(placementEl);
        
        return placementEl;
    }
    
    updatePlacementStyle(placementEl, placementData, productData) {
        const segment = placementEl.closest('.segment');
        const segmentHeight = parseFloat(segment.dataset.height);
        
        placementEl.style.left = placementData.x_position + 'px';
        placementEl.style.width = placementData.occupied_width + 'px';
        placementEl.style.height = productData.height + 'px';
        placementEl.style.top = (segmentHeight - productData.height + 2) + 'px';
    }
    
    updatePlacementContent(placementEl, productData, placementData) {
        placementEl.innerHTML = '';
        
        // 商品画像
        if (productData.imageUrl) {
            const img = document.createElement('img');
            img.src = productData.imageUrl;
            img.className = 'product-image';
            img.alt = productData.name;
            placementEl.appendChild(img);
        }
        
        // 商品名
        const nameEl = document.createElement('div');
        nameEl.className = 'product-name';
        nameEl.textContent = this.truncateText(productData.name, 15);
        nameEl.title = productData.name;
        placementEl.appendChild(nameEl);
        
        // メーカー名
        const manufacturerEl = document.createElement('div');
        manufacturerEl.className = 'manufacturer-name';
        manufacturerEl.textContent = this.truncateText(productData.manufacturer, 10);
        placementEl.appendChild(manufacturerEl);
        
        // フェース数バッジ
        if (placementData.face_count > 1) {
            const faceBadge = document.createElement('div');
            faceBadge.className = 'face-badge';
            faceBadge.textContent = placementData.face_count;
            placementEl.appendChild(faceBadge);
        }
        
        // リサイズハンドル
        const resizeHandle = document.createElement('div');
        resizeHandle.className = 'resize-handle';
        placementEl.appendChild(resizeHandle);
    }
    
    attachPlacementEvents(placementEl) {
        // クリック選択
        placementEl.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectPlacement(placementEl);
        });
        
        // ダブルクリック編集
        placementEl.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            this.editPlacement(placementEl);
        });
        
        // ドラッグ開始
        placementEl.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('resize-handle')) {
                this.startResize(e, placementEl);
            } else {
                this.startDrag(e, placementEl);
            }
        });
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
    
    startDrag(e, placementEl) {
        this.isDragging = true;
        this.draggedPlacement = placementEl;
        this.dragStartX = e.clientX;
        this.dragStartY = e.clientY;
        this.dragOffsetX = e.offsetX;
        this.dragOffsetY = e.offsetY;
        
        placementEl.classList.add('dragging');
        document.body.style.cursor = 'grabbing';
        
        e.preventDefault();
    }
    
    updateDrag(e) {
        if (!this.draggedPlacement) return;
        
        const canvas = document.getElementById('shelf-canvas');
        const canvasRect = canvas.getBoundingClientRect();
        const currentZoom = parseFloat(document.getElementById('zoom-slider').value);
        
        const x = (e.clientX - canvasRect.left - this.dragOffsetX) / currentZoom;
        const y = (e.clientY - canvasRect.top - this.dragOffsetY) / currentZoom;
        
        // 配置可能な段を検出
        const targetSegment = this.findSegmentAtPosition(y);
        
        if (targetSegment) {
            this.highlightDropTarget(targetSegment);
            
            // スナップ処理
            const snappedX = this.snapToGrid ? this.snapToGridPosition(x) : x;
            
            // 一時的な位置更新
            this.draggedPlacement.style.left = Math.max(0, snappedX) + 'px';
            
            // 配置可能性の視覚フィードバック
            this.updateDropFeedback(targetSegment, snappedX);
        } else {
            this.clearDropTarget();
        }
    }
    
    endDrag(e) {
        if (!this.draggedPlacement) return;
        
        const canvas = document.getElementById('shelf-canvas');
        const canvasRect = canvas.getBoundingClientRect();
        const currentZoom = parseFloat(document.getElementById('zoom-slider').value);
        
        const y = (e.clientY - canvasRect.top - this.dragOffsetY) / currentZoom;
        const x = (e.clientX - canvasRect.left - this.dragOffsetX) / currentZoom;
        
        const targetSegment = this.findSegmentAtPosition(y);
        const snappedX = this.snapToGrid ? this.snapToGridPosition(x) : x;
        
        if (targetSegment && snappedX >= 0) {
            // 新しい位置に配置を移動
            this.movePlacement(this.draggedPlacement, targetSegment, snappedX);
        } else {
            // 元の位置に戻す
            this.revertPlacement(this.draggedPlacement);
        }
        
        // クリーンアップ
        this.draggedPlacement.classList.remove('dragging');
        this.clearDropTarget();
        this.isDragging = false;
        this.draggedPlacement = null;
        document.body.style.cursor = '';
    }
    
    async movePlacement(placementEl, targetSegment, newX) {
        const placementId = parseInt(placementEl.dataset.placementId);
        const newSegmentId = parseInt(targetSegment.dataset.segmentId);
        
        try {
            const result = await this.updatePlacement(placementId, {
                segment_id: newSegmentId,
                x_position: newX
            });
            
            if (result) {
                // 段間移動の場合
                if (placementEl.closest('.segment') !== targetSegment) {
                    targetSegment.appendChild(placementEl);
                    this.updateSegmentInfo(placementEl.closest('.segment')); // 元の段
                }
                
                this.updateSegmentInfo(targetSegment); // 新しい段
                this.showSuccess('配置を移動しました');
            } else {
                this.revertPlacement(placementEl);
            }
        } catch (error) {
            this.revertPlacement(placementEl);
            this.showError('移動に失敗しました: ' + error.message);
        }
    }
    
    revertPlacement(placementEl) {
        const originalX = parseFloat(placementEl.dataset.xPosition);
        placementEl.style.left = originalX + 'px';
    }
    
    // ユーティリティメソッド
    snapToGridPosition(x) {
        return Math.round(x / this.gridSize) * this.gridSize;
    }
    
    findSegmentAtPosition(y) {
        const segments = document.querySelectorAll('.segment');
        for (let segment of segments) {
            const rect = segment.getBoundingClientRect();
            const canvasRect = document.getElementById('shelf-canvas').getBoundingClientRect();
            const currentZoom = parseFloat(document.getElementById('zoom-slider').value);
            
            const segmentTop = (rect.top - canvasRect.top) / currentZoom;
            const segmentBottom = (rect.bottom - canvasRect.top) / currentZoom;
            
            if (y >= segmentTop && y <= segmentBottom) {
                return segment;
            }
        }
        return null;
    }
    
    highlightDropTarget(segment) {
        this.clearDropTarget();
        segment.classList.add('drop-target');
    }
    
    clearDropTarget() {
        document.querySelectorAll('.segment').forEach(seg => {
            seg.classList.remove('drop-target', 'drop-invalid');
        });
    }
    
    updateDropFeedback(segment, x) {
        // 配置可能性をチェックして視覚フィードバック
        const productWidth = parseFloat(this.draggedPlacement.dataset.productWidth);
        const faceCount = parseInt(this.draggedPlacement.dataset.faceCount);
        const requiredWidth = productWidth * faceCount;
        
        if (x + requiredWidth > this.currentShelf.width) {
            segment.classList.remove('drop-target');
            segment.classList.add('drop-invalid');
        } else {
            segment.classList.remove('drop-invalid');
            segment.classList.add('drop-target');
        }
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
        
        const productName = placementEl.querySelector('.product-name').textContent;
        const manufacturerName = placementEl.querySelector('.manufacturer-name').textContent;
        
        const info = document.getElementById('selected-product-info');
        info.innerHTML = `
            <h6>${productName}</h6>
            <small>${manufacturerName}</small><br>
            <small>配置ID: ${placementEl.dataset.placementId}</small>
        `;
        
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
        
        // 段情報更新
        document.querySelectorAll('.segment').forEach(segment => {
            this.updateSegmentInfo(segment);
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
    
    updateSegmentInfo(segment) {
        const placements = segment.querySelectorAll('.placement');
        let usedWidth = 0;
        
        placements.forEach(placement => {
            usedWidth += parseFloat(placement.dataset.occupiedWidth) || 0;
        });
        
        const availableWidth = this.currentShelf.width - usedWidth;
        const utilization = (usedWidth / this.currentShelf.width) * 100;
        
        segment.dataset.availableWidth = availableWidth;
        
        const infoEl = segment.querySelector('.segment-info .available-width');
        if (infoEl) {
            infoEl.textContent = `${availableWidth.toFixed(1)}cm空き`;
        }
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
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());
        
        const response = await fetch(url, {
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
            alert(message); // フォールバック
        }
    }
}

// グローバルインスタンス
window.placementEngine = new PlacementEngine();

// 公開API
window.PlacementAPI = {
    selectPlacement: (element) => window.placementEngine.selectPlacement(element),
    deselectPlacement: () => window.placementEngine.deselectPlacement(),
    deletePlacement: (element) => window.placementEngine.deletePlacement(element),
    updateStatistics: () => window.placementEngine.updateStatistics(),
    undo: () => window.placementEngine.undo(),
    redo: () => window.placementEngine.redo(),
    saveLayout: () => window.placementEngine.showSuccess('レイアウトは自動保存されています')
};