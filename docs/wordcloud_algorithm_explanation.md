# ワードクラウド作成アルゴリズム解説

## 📌 概要

ワードクラウド（Word Cloud）は、テキストデータ内の単語の出現頻度を視覚的に表現する手法です。
頻出単語ほど大きく、低頻度の単語ほど小さく表示されます。

## 🔄 処理フロー

### 1. データ入力
```
生テキスト → 前処理 → 単語分割 → 頻度計算 → レイアウト → 画像生成
```

## 📝 詳細な処理ステップ

### Step 1: テキストデータの準備

#### 入力データ例（東京高専プロジェクト）
```python
# Before（授業前）
"みそに塩が入っているから"
"みその中にしょっぱくなる成分が入っているから"
"塩が使われているから"

# After（授業後）
"ナトリウムが入っているから"
"塩化ナトリウムが含まれているから"
"ナトリウムが入っているから"
```

### Step 2: テキスト前処理

#### 2.1 正規化処理
```python
def normalize_text(text):
    # 全角・半角統一
    text = unicodedata.normalize('NFKC', text)
    
    # 小文字化（英語の場合）
    text = text.lower()
    
    # 不要な空白の除去
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

#### 2.2 日本語特有の処理
```python
# 表記ゆれの統一
normalization_rules = {
    "みそしる": "みそ汁",
    "しお": "塩",
    "えん分": "塩分"
}
```

### Step 3: 形態素解析（単語分割）

#### 3.1 janome/MeCabによる分割
```python
from janome.tokenizer import Tokenizer

tokenizer = Tokenizer()
text = "ナトリウムが入っているから"

# 形態素解析結果
tokens = list(tokenizer.tokenize(text))
# → ['ナトリウム', 'が', '入っ', 'て', 'いる', 'から']
```

#### 3.2 品詞フィルタリング
```python
# 意味のある品詞のみ抽出
meaningful_pos = ['名詞', '動詞', '形容詞']

filtered_words = []
for token in tokens:
    pos = token.part_of_speech.split(',')[0]
    if pos in meaningful_pos:
        filtered_words.append(token.surface)
# → ['ナトリウム', '入っ']
```

### Step 4: 単語頻度計算

#### 4.1 頻度カウント
```python
from collections import Counter

# 全テキストから単語を収集
all_words = ['ナトリウム', '塩', 'ナトリウム', '実験', 'ナトリウム', ...]

# 頻度計算
word_freq = Counter(all_words)
# → {'ナトリウム': 40, '塩': 37, '実験': 16, ...}
```

#### 4.2 頻度の正規化とフィルタリング
```python
# 最小・最大頻度でフィルタリング
min_count = 2  # 2回以上出現
max_count = 100  # 極端に多い単語を除外

# ストップワード除去
stopwords = ['する', 'なる', 'ある', 'いる', 'です', 'ます']

filtered_freq = {
    word: count 
    for word, count in word_freq.items()
    if min_count <= count <= max_count
    and word not in stopwords
}
```

### Step 5: レイアウトアルゴリズム

#### 5.1 フォントサイズ計算
```python
def calculate_font_size(word_freq, word, min_size=10, max_size=100):
    # 頻度に基づくサイズ計算
    max_freq = max(word_freq.values())
    min_freq = min(word_freq.values())
    
    # 線形スケーリング
    freq = word_freq[word]
    normalized = (freq - min_freq) / (max_freq - min_freq)
    
    # relative_scalingパラメータで調整
    relative_scaling = 0.5
    size = min_size + (max_size - min_size) * (normalized ** relative_scaling)
    
    return int(size)
```

#### 5.2 スパイラル配置アルゴリズム
```python
def spiral_layout(words_with_sizes):
    """
    アルキメデスの螺旋に沿って単語を配置
    中心から外側に向かって配置位置を探索
    """
    positions = []
    center_x, center_y = width/2, height/2
    
    for word, size in words_with_sizes:
        # 螺旋のパラメータ
        theta = 0  # 角度
        radius = 0  # 半径
        
        while True:
            # 螺旋上の座標計算
            x = center_x + radius * cos(theta)
            y = center_y + radius * sin(theta)
            
            # 衝突判定
            if not check_collision(word, size, x, y, positions):
                positions.append((word, size, x, y))
                break
            
            # 次の位置へ
            theta += 0.1
            radius = theta * 2  # アルキメデスの螺旋
```

#### 5.3 衝突検出
```python
def check_collision(word, size, x, y, existing_positions):
    """
    既存の単語と重なるかチェック
    バウンディングボックスベースの判定
    """
    word_width = len(word) * size * 0.6  # 概算
    word_height = size
    
    for other_word, other_size, other_x, other_y in existing_positions:
        other_width = len(other_word) * other_size * 0.6
        other_height = other_size
        
        # 矩形の重なり判定
        if (abs(x - other_x) < (word_width + other_width) / 2 and
            abs(y - other_y) < (word_height + other_height) / 2):
            return True  # 衝突あり
    
    return False  # 衝突なし
```

### Step 6: 色の割り当て

#### 6.1 カラーマップ適用
```python
import matplotlib.cm as cm

def assign_colors(words_with_freq, colormap='viridis'):
    # カラーマップ取得
    cmap = cm.get_cmap(colormap)
    
    # 頻度でソート
    sorted_words = sorted(words_with_freq.items(), 
                         key=lambda x: x[1], reverse=True)
    
    colors = {}
    for i, (word, freq) in enumerate(sorted_words):
        # 0.0〜1.0の範囲に正規化
        color_value = i / len(sorted_words)
        # RGB値取得
        colors[word] = cmap(color_value)
    
    return colors
```

### Step 7: 画像レンダリング

#### 7.1 マスク処理（オプション）
```python
# 画像マスクを使用した形状制御
mask = np.array(Image.open("mask_image.png"))
wordcloud = WordCloud(mask=mask).generate_from_frequencies(word_freq)
```

#### 7.2 最終レンダリング
```python
from PIL import Image, ImageDraw, ImageFont

def render_wordcloud(positions, colors, font_path):
    # キャンバス作成
    img = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(img)
    
    for word, size, x, y in positions:
        # フォント設定
        font = ImageFont.truetype(font_path, size=size)
        
        # 色取得
        color = colors[word]
        
        # 回転（prefer_horizontalパラメータに基づく）
        if random.random() > prefer_horizontal:
            # 垂直配置
            img_word = Image.new('RGBA', (size*len(word), size), (0,0,0,0))
            draw_word = ImageDraw.Draw(img_word)
            draw_word.text((0,0), word, font=font, fill=color)
            img_word = img_word.rotate(90, expand=1)
            img.paste(img_word, (int(x), int(y)), img_word)
        else:
            # 水平配置
            draw.text((x, y), word, font=font, fill=color)
    
    return img
```

## 🎯 最適化テクニック

### 1. 階層的配置
```python
# 重要度順に配置
# 1. 最頻出単語を中心に配置
# 2. 次に頻出の単語を周辺に配置
# 3. 低頻度単語は外側に配置
```

### 2. 四分木（Quadtree）による空間分割
```python
class QuadTree:
    """
    空間を4分割して効率的な衝突検出
    O(n²) → O(n log n)の計算量削減
    """
    def __init__(self, boundary):
        self.boundary = boundary
        self.words = []
        self.divided = False
        self.children = []
```

### 3. 密度調整
```python
# relative_scalingによる調整
# 0.0: 全単語同じサイズ
# 0.5: 中間的なサイズ差（デフォルト）
# 1.0: 頻度差を最大限反映
```

## 📊 プロジェクトでの実装例

### 東京高専データの処理
```python
# 1. 授業前後のテキストデータ
before_texts = ["みそに塩が入っている", ...]  # 84件
after_texts = ["ナトリウムが入っている", ...]   # 95件

# 2. 形態素解析と頻度計算
before_freq = analyze_frequency(before_texts)
after_freq = analyze_frequency(after_texts)

# 3. 教育効果の可視化
# Beforeワードクラウド: 「みそ」「塩」が大きく表示
# Afterワードクラウド: 「ナトリウム」が大きく表示

# 4. パラメータ調整による最適化
config = {
    'font_path': 'fonts/ipaexg.ttf',  # 日本語フォント
    'width': 800,
    'height': 400,
    'max_words': 100,
    'background_color': 'white',
    'colormap': 'viridis',
    'prefer_horizontal': 0.7,  # 70%を水平配置
    'relative_scaling': 0.5
}
```

## 🔍 品質向上のポイント

### 1. 日本語処理の工夫
- 複合語の適切な分割（例：「塩化ナトリウム」を一語として扱う）
- 同義語の統一（例：「Na」「ナトリウム」を統合）
- 助詞の除去による意味語の強調

### 2. 視認性の向上
- 背景色とのコントラスト確保
- フォントサイズの適切な範囲設定
- 単語間の適切な間隔

### 3. 情報量の最適化
- max_words設定による過密防止
- min_font_sizeによる可読性確保
- 重要語の中心配置

## 📈 アルゴリズムの計算量

- **形態素解析**: O(n×m) （n:文書数、m:平均文長）
- **頻度計算**: O(n)
- **レイアウト**: O(k²)〜O(k log k) （k:表示単語数）
- **レンダリング**: O(k)

**全体**: O(n×m + k²) ≈ O(n×m)（通常k << n×m）

## 🎨 視覚的効果

1. **サイズによる重要度表現**: 頻出語ほど大きく表示
2. **色による分類**: カラーマップで頻度や品詞を表現
3. **配置による関連性**: 中心ほど重要、周辺は補助的
4. **密度による印象**: 疎密で文書の多様性を表現

このアルゴリズムにより、大量のテキストデータから直感的に理解できる視覚表現を生成し、
東京高専プロジェクトでは「教育効果の可視化」を実現しています。