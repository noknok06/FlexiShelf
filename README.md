# FlexiShelf - 次世代棚割りアプリケーション 設計書

## プロジェクト概要

基本情報

プロジェクト名: FlexiShelf
目的: リアルなスーパー棚陳列を再現する柔軟な棚割りシステム
技術スタック: Django 4.2+, PostgreSQL, Bootstrap 5, Vanilla JS
特徴: セグメント式段管理、フレキシブル配置、リアルサイズ対応

## プロジェクト構造

"""

flexishelf/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/                          # プロジェクト設定
│   ├── __init__.py
│   ├── settings.py                  # 統合設定ファイル
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                            # アプリケーション群
│   ├── __init__.py
│   ├── core/                        # 共通機能
│   │   ├── __init__.py
│   │   ├── models.py                # 抽象基底モデル
│   │   ├── mixins.py                # 共通ミックスイン
│   │   └── validators.py            # 基本バリデーター
│   │
│   ├── accounts/                    # ユーザー管理
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── products/                    # 商品管理
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── services.py              # 基本ビジネスロジック
│   │
│   ├── shelves/                     # 棚・陳列管理
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── services.py
│   │   └── constraints.py           # 基本配置制約
│   │
│   └── proposals/                   # 提案管理
│       ├── __init__.py
│       ├── models.py
│       ├── views.py
│       ├── forms.py
│       ├── urls.py
│       ├── admin.py
│       └── exporters.py             # 基本エクスポート機能
│
├── static/                          # 静的ファイル
│   ├── css/
│   │   ├── base.css                 # 基本スタイル
│   │   ├── components.css           # 汎用コンポーネント
│   │   └── shelf-layout.css         # 棚レイアウト専用
│   ├── js/
│   │   ├── base.js                  # 基本JS機能
│   │   ├── components/              # 再利用可能コンポーネント
│   │   │   ├── modal.js
│   │   │   ├── toast.js
│   │   │   └── drag-drop.js
│   │   └── shelf/                   # 棚機能専用
│   │       ├── placement-engine.js  # 基本配置エンジン
│   │       └── segment-manager.js   # 段管理
│   ├── images/
│   │   ├── icons/
│   │   └── placeholders/
│   └── vendor/                      # 外部ライブラリ
│       └── bootstrap/
│
├── templates/                       # テンプレート
│   ├── base/
│   │   ├── base.html               # 基底テンプレート
│   │   └── components/             # 基本コンポーネント
│   │       ├── navbar.html
│   │       ├── breadcrumb.html
│   │       └── pagination.html
│   ├── accounts/
│   │   ├── login.html
│   │   └── register.html
│   ├── products/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── form.html
│   ├── shelves/
│   │   ├── list.html
│   │   ├── detail.html
│   │   ├── form.html
│   │   └── placement/
│   │       └── placement-canvas.html
│   └── proposals/
│       ├── list.html
│       ├── detail.html
│       └── form.html
│
├── media/                           # アップロードファイル
│   ├── products/
│   │   └── images/
│   └── exports/
│
└── utils/                          # 基本ユーティリティ
    ├── __init__.py
    ├── image_processor.py          # 基本画像処理
    └── exporters.py                # 基本エクスポート

"""

## 棚割り機能 詳細要件定義

1. 棚割り機能概要

1.1 目的

実際のスーパーの棚を正確にデジタル再現
商品の物理サイズを考慮した配置システム
フェーシング（同一商品の横並び）による実際の陳列状況の表現
段別管理による柔軟な棚構成

1.2 基本概念

棚（Shelf）: 物理的な棚の器
段（Segment）: 棚板で区切られた各階層
配置（Placement）: 段内での商品の位置と数量
フェーシング: 同一商品の横並び配置数

2. 棚構造管理

2.1 棚基本情報

2.1.1 必須項目

# 棚マスタ

name = models.CharField('棚名', max_length=100)           # 例: "エンド陳列棚A"
width = models.FloatField('幅(cm)')                      # 例: 120.0
depth = models.FloatField('奥行(cm)')                    # 例: 40.0
description = models.TextField('説明', blank=True)       # 設置場所、特徴等

2.1.2 棚作成フロー

基本情報入力: 棚名、寸法入力
段構成設定: 段数と各段の高さ設定
プレビュー確認: 作成される棚の視覚確認
作成実行: 棚と段の一括作成

2.2 段（セグメント）管理

2.2.1 段の属性

# 段マスタ

level = models.IntegerField('段番号')                    # 1=最下段, 2,3,4...
height = models.FloatField('段高さ(cm)')                 # 例: 35.0
y_position = models.FloatField('床からの位置(cm)')        # 自動計算

2.2.2 段高さ調整機能

個別調整: 各段の高さを独立して調整可能
制約チェック: 配置済み商品が収まるかの自動検証
再配置提案: 収まらない商品の移動先提案

段高さ調整UI仕様:
段1: [▼ 25cm ▲] ← スライダーまたは数値入力
段2: [▼ 30cm ▲]
段3: [▼ 35cm ▲]
段4: [▼ 40cm ▲]

3. 商品配置システム

3.1 配置の基本概念

3.1.1 座標系

X座標: 段内での左端からの距離（cm）
Y座標: 段レベルで管理（段番号で指定）
占有幅: 商品幅 × フェース数

3.1.2 配置データモデル

class ProductPlacement(models.Model):
    shelf = models.ForeignKey(Shelf)                     # 対象棚
    segment = models.ForeignKey(ShelfSegment)            # 対象段
    product = models.ForeignKey(Product)                 # 配置商品
    x_position = models.FloatField('X座標(cm)')          # 段内位置
    face_count = models.IntegerField('フェース数')        # 横並び数
    occupied_width = models.FloatField('占有幅(cm)')      # 自動計算

3.2 配置操作方法

3.2.1 配置方法の選択肢

クリック配置: 商品選択 → 配置位置クリック
ドラッグ&ドロップ: 商品パレットから棚へドラッグ
座標入力: 正確な位置を数値指定

3.2.2 配置操作フロー

1. 商品選択
   ↓
2. 配置可能段の表示（高さ制約による自動フィルタ）
   ↓
3. 段選択 & 位置指定
   ↓
4. フェース数設定
   ↓
5. 制約チェック（重複・幅超過等）
   ↓
6. 配置実行 または エラー表示

3.3 配置制約システム

3.3.1 物理制約

高さ制約
def check_height_constraint(product, segment):
    return product.height <= segment.height
幅制約
def check_width_constraint(product, segment, x_position, face_count):
    required_width = product.width * face_count
    return x_position + required_width <= segment.shelf.width
重複制約
def check_overlap_constraint(segment, x_position, face_count, product):
    new_start = x_position
    new_end = x_position + (product.width * face_count)
    
    for existing in segment.placements.all():
        existing_start = existing.x_position
        existing_end = existing.x_position + existing.occupied_width
        
        # 重複判定
        if not (new_end <= existing_start or new_start >= existing_end):
            return False
    return True

3.3.2 エラーメッセージ

"商品の高さ（25.0cm）が段の高さ（20.0cm）を超えています"
"配置位置が棚の幅（120.0cm）を超えています"
"他の商品（○○洗剤）と配置が重複しています"
"フェース数が多すぎます（最大3フェース推奨）"

4. フェーシング機能

4.1 フェーシングの概念

4.1.1 定義

同一商品を横に並べて配置すること

1フェース: 商品1個分の幅
3フェース: 同じ商品を3個横並び（商品幅×3の占有）

4.1.2 フェーシング設定

# 商品マスタでの制約設定

min_faces = models.IntegerField('最小フェース数', default=1)      # 最低配置数
max_faces = models.IntegerField('最大フェース数', default=10)     # 最大配置数
recommended_faces = models.IntegerField('推奨フェース数', default=1) # 推奨配置数

4.2 フェーシング操作

4.2.1 フェース数変更UI

配置時設定

商品選択: [コカ・コーラ 500ml]
フェース数: [1] [2] [3] [4] [5] ← クリックまたはスライダー
占有幅プレビュー: 19.5cm (6.5cm × 3個)
配置後変更
html配置済み商品クリック → フェース数編集ダイアログ
現在: 3フェース (19.5cm)
変更: [1] [2] [3] [4] [5]
4.2.2 フェーシング制約

商品制約: 商品ごとの最大・最小フェース数
段幅制約: 段の残り幅に収まる最大フェース数
実用制約: 極端に多いフェース数への警告

4.3 フェース数最適化


4.3.1 自動提案機能

def suggest_optimal_facing(product, segment, x_position):
    """最適フェース数の提案"""
    available_width = segment.shelf.width - x_position
    max_possible = int(available_width // product.width)
    
    # 制約を考慮した提案
    return min(
        max_possible,
        product.max_faces,
        product.recommended_faces + 2  # 推奨+α
    )

1. 棚割り表示システム

5.1 表示モード

5.1.1 キャンバス表示

2D平面表示: 棚を真正面から見た状態
スケール自動調整: 棚サイズに応じた表示倍率
段別色分け: 段ごとの背景色変更オプション

5.1.2 表示要素

<!-- 棚全体 -->
<div class="shelf-canvas" style="width: 240px; height: 200px;">
  
  <!-- 段1 (最下段) -->
  <div class="segment" data-level="1" style="height: 50px;">
    <div class="segment-label">段1</div>
    
    <!-- 商品配置 -->
    <div class="placement own-product" style="left: 0px; width: 39px;">
      <img src="cola.jpg" />
      <div class="product-name">コカ・コーラ</div>
      <div class="face-badge">3</div>
    </div>
  </div>
  
  <!-- 段2 -->
  <div class="segment" data-level="2" style="height: 40px;">
    <!-- ... -->
  </div>
  
</div>

5.2 商品表示

5.2.1 商品表示要素

商品画像: サムネイル表示
商品名: 短縮表示（15文字程度）
メーカー名: 小さく表示
フェース数バッジ: 2個以上の場合に表示
区分色: 自社/競合の色分け

5.2.2 表示スタイル

.placement.own-product {
    background-color: #d4edda;    /* 自社商品: 薄緑 */
    border: 2px solid #c3e6cb;
}

.placement.competitor-product {
    background-color: #fff3cd;    /* 競合商品: 薄黄 */
    border: 2px solid #ffeaa7;
}

.face-badge {
    position: absolute;
    top: 2px;
    right: 2px;
    background: #007bff;
    color: white;
    border-radius: 50%;
    width: 16px;
    height: 16px;
    font-size: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}

1. 操作インターフェース

6.1 棚割り編集画面構成

<!--- 画面レイアウト --->
<div class="shelf-editor">
  
  <!-- 左パネル: 商品選択 -->
  <div class="product-panel">
    <div class="search-box">商品検索</div>
    <div class="category-filter">カテゴリフィルタ</div>
    <div class="product-list">
      <!-- 商品一覧（ドラッグ可能） -->
    </div>
  </div>
  
  <!-- 中央: 棚キャンバス -->
  <div class="main-canvas">
    <div class="toolbar">
      <button class="save-btn">保存</button>
      <button class="reset-btn">リセット</button>
      <select class="view-mode">表示モード</select>
    </div>
    <div class="shelf-canvas" id="shelf-canvas">
      <!-- 棚割り表示エリア -->
    </div>
  </div>
  
  <!-- 右パネル: 段管理・統計 -->
  <div class="control-panel">
    <div class="segment-controls">
      <!-- 段高さ調整 -->
    </div>
    <div class="placement-stats">
      <!-- 配置統計 -->
    </div>
  </div>
  
</div>

6.2 商品選択パネル

6.2.1 商品一覧表示

<div class="product-item" data-product-id="123" draggable="true">
  <img src="product.jpg" class="product-thumb" />
  <div class="product-info">
    <div class="product-name">コカ・コーラ 500ml</div>
    <div class="product-size">6.5×20.5×6.5cm</div>
    <div class="product-maker">コカ・コーラ</div>
    <div class="own-flag">自社</div>
  </div>
</div>

6.2.2 検索・フィルタ機能

テキスト検索: 商品名、JANコード、メーカー名
カテゴリフィルタ: 飲料、菓子、日用品等
サイズフィルタ: 大型、中型、小型
区分フィルタ: 自社商品、競合商品

6.3 段管理パネル
6.3.1 段高さ調整UI

<div class="segment-controls">
  <h5>段高さ調整</h5>
  
  <div class="segment-control" data-level="4">
    <label>段4: </label>
    <input type="range" min="10" max="60" value="30" class="height-slider" />
    <input type="number" min="10" max="60" value="30" class="height-input" />
    <span class="unit">cm</span>
  </div>
  
  <div class="segment-control" data-level="3">
    <label>段3: </label>
    <input type="range" min="10" max="60" value="25" class="height-slider" />
    <input type="number" min="10" max="60" value="25" class="height-input" />
    <span class="unit">cm</span>
  </div>
  
  <!-- ... 他の段 ... -->
  
  <button class="apply-heights">高さ変更を適用</button>
</div>

1. データ永続化

7.1 保存タイミング

7.1.1 自動保存

配置操作後: 商品配置・削除・移動後の即座保存
フェース数変更後: フェース数変更の即座保存
段高さ変更後: 段高さ調整の即座保存

7.1.2 手動保存

一括保存ボタン: 複数変更をまとめて保存
下書き保存: 作業途中の状態保存

7.2 データ整合性
7.2.1 トランザクション管理

def update_placement(placement_id, **kwargs):
    """配置更新（トランザクション保証）"""
    placement = ProductPlacement.objects.select_for_update().get(id=placement_id)
    
    # 制約チェック
    if not validate_placement_constraints(placement, **kwargs):
        raise ValidationError("配置制約違反")
    
    # 更新実行
    for key, value in kwargs.items():
        setattr(placement, key, value)
    
    placement.save()
    return placement

1. エラーハンドリング・バリデーション

8.1 リアルタイムバリデーション

8.1.1 配置可能性の事前チェック

// 商品選択時の配置可能段の表示
function highlightValidSegments(productId) {
    fetch(`/api/products/${productId}/valid-segments/`)
        .then(response => response.json())
        .then(data => {
            document.querySelectorAll('.segment').forEach(segment => {
                const level = segment.dataset.level;
                if (data.valid_levels.includes(parseInt(level))) {
                    segment.classList.add('placement-valid');
                } else {
                    segment.classList.add('placement-invalid');
                }
            });
        });
}
8.2 ユーザーフィードバック
8.2.1 視覚的フィードバック

配置可能エリア: 緑色ハイライト
配置不可エリア: 赤色ハイライト
警告エリア: 黄色ハイライト（推奨外だが配置可能）

8.2.2 エラーメッセージ
const ERROR_MESSAGES = {
    HEIGHT_EXCEEDED: '商品の高さが段の高さを超えています',
    WIDTH_EXCEEDED: '棚の幅を超えています', 
    OVERLAP_DETECTED: '他の商品と重複しています',
    INVALID_FACE_COUNT: 'フェース数が範囲外です',
    SEGMENT_NOT_FOUND: '対象の段が見つかりません'
};