# 環境セットアップガイド
## 東京高専出前授業テキストマイニング分析環境

**最終更新**: 2025-05-31  
**対象OS**: Linux (WSL2), macOS, Windows  
**Python要件**: 3.8+  

## 🚀 クイックスタート

### 1. 基本環境確認
```bash
# Python バージョン確認
python --version  # 3.8+ 必須

# 作業ディレクトリに移動
cd /home/grace/projects/social-implement/lecture-survey-analysis/lecture-text-analysis

# 仮想環境作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
```

### 2. 依存関係インストール
```bash
# 基本パッケージ
pip install --upgrade pip
pip install -r requirements.txt

# 追加分析パッケージ
pip install fugashi unidic-lite plotly kaleido pingouin statsmodels
```

### 3. 日本語NLP環境セットアップ

#### Option A: MeCab（高精度、権限問題の可能性）
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install mecab mecab-ipadic-utf8 libmecab-dev

# macOS
brew install mecab mecab-ipadic

# Python バインディング
pip install mecab-python3
```

**権限問題が発生した場合**: Option B（janome）を使用

#### Option B: janome（純Python、権限問題なし）
```bash
# janomeは requirements.txt に含有済み
# 設定不要、即利用可能
```

### 4. 環境検証
```bash
# 検証スクリプト実行
python scripts/setup/validate_environment.py
```

## 📦 詳細インストール手順

### 依存関係の詳細説明

#### 必須パッケージ
```txt
# データ処理・基本分析
pandas>=2.0.0           # データフレーム操作
numpy>=1.24.0            # 数値計算
scipy>=1.11.0            # 統計計算

# 自然言語処理
janome>=0.5.0            # 日本語形態素解析（純Python）
spacy>=3.5.0             # NLP pipeline
ginza>=5.1.0             # 日本語spaCyモデル

# 可視化
matplotlib>=3.7.0        # 基本図表
seaborn>=0.12.0          # 統計的可視化
wordcloud>=1.9.0         # ワードクラウド

# 機械学習
scikit-learn>=1.3.0      # 機械学習・クラスタリング
gensim>=4.3.0            # トピックモデリング

# 統計分析
textblob>=0.17.0         # 感情分析
```

#### 拡張パッケージ
```txt
# 高度統計分析
pingouin>=0.5.3          # 統計検定・効果量
statsmodels>=0.14.0      # 回帰分析・時系列

# 高度可視化
plotly>=5.15.0           # インタラクティブ図表
kaleido>=0.2.1           # 静的画像出力

# 日本語処理強化
fugashi>=1.3.0           # MeCabラッパー（高速）
unidic-lite>=1.0.8       # UniDic辞書（軽量版）
```

### トラブルシューティング

#### 1. MeCab インストール失敗
**症状**: `sudo: command not found` または権限エラー
```bash
# 解決法1: janome使用（推奨）
# requirements.txt のjanomeを使用、設定変更不要

# 解決法2: ユーザーレベルインストール（権限問題回避）
# conda/miniconda使用
conda install -c conda-forge mecab mecab-ipadic

# 解決法3: 手動権限要請
echo "MeCab installation requires system privileges. Please request manual installation."
```

#### 2. spaCy/ginza モデルダウンロード失敗
```bash
# 手動ダウンロード
python -m spacy download ja_ginza
python -m spacy download ja_ginza_electra

# プロキシ環境対応
pip install --proxy http://proxy.server:port ja-ginza
```

#### 3. メモリ不足エラー
```bash
# 大規模データ処理時の対策
export PYTHONHASHSEED=0
ulimit -v 4194304  # メモリ制限設定（4GB）

# バッチサイズ調整
# config/analysis_config.yaml 内で chunk_size を削減
```

#### 4. 文字エンコーディング問題
```bash
# 環境変数設定
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8

# Python内での設定確認
python -c "import locale; print(locale.getpreferredencoding())"
```

## 🧪 環境検証・テストスイート

### 自動検証スクリプト
**scripts/setup/validate_environment.py** の作成:
```python
#!/usr/bin/env python3
"""
環境検証スクリプト
実行: python scripts/setup/validate_environment.py
"""

import sys
import importlib
import subprocess
from pathlib import Path

def check_python_version():
    """Python バージョン確認"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - 3.8+ required")
        return False

def check_package(package_name, import_name=None):
    """パッケージ存在確認"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {package_name} {version} - OK")
        return True
    except ImportError:
        print(f"✗ {package_name} - NOT FOUND")
        return False

def check_japanese_nlp():
    """日本語NLP環境確認"""
    # janome テスト
    try:
        from janome.tokenizer import Tokenizer
        tokenizer = Tokenizer()
        tokens = list(tokenizer.tokenize("これはテストです"))
        print("✓ janome - Japanese tokenization OK")
        return True
    except:
        print("✗ janome - Japanese tokenization FAILED")
        return False

def check_data_files():
    """データファイル存在確認"""
    required_files = [
        "data/raw/comments.csv",
        "data/raw/q2_reasons_before.csv", 
        "data/raw/q2_reasons_after.csv"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} - EXISTS")
        else:
            print(f"✗ {file_path} - NOT FOUND")
            all_exist = False
    
    return all_exist

def check_output_directories():
    """出力ディレクトリ確認"""
    required_dirs = [
        "outputs/wordclouds",
        "outputs/sentiment_results",
        "outputs/topic_models"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ {dir_path} - READY")

def main():
    """メイン検証実行"""
    print("=== 環境検証開始 ===\n")
    
    # Python バージョン
    python_ok = check_python_version()
    
    # 必須パッケージ
    packages = [
        "pandas", "numpy", "scipy", "matplotlib", "seaborn",
        "sklearn", "gensim", "janome", "textblob", "wordcloud"
    ]
    
    packages_ok = all(check_package(pkg) for pkg in packages)
    
    # 日本語NLP
    nlp_ok = check_japanese_nlp()
    
    # データファイル
    data_ok = check_data_files()
    
    # 出力ディレクトリ
    check_output_directories()
    
    # 総合判定
    if all([python_ok, packages_ok, nlp_ok, data_ok]):
        print("\n✓ 全環境確認完了 - 分析実行可能")
        return True
    else:
        print("\n✗ 環境不備あり - 上記エラーを解決してください")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

### 段階的テスト実行
```bash
# Phase 1: 基本環境
python scripts/setup/validate_environment.py

# Phase 2: データ読み込みテスト
python -c "
import pandas as pd
df = pd.read_csv('data/raw/comments.csv')
print(f'Comments loaded: {len(df)} records')
"

# Phase 3: 日本語処理テスト
python -c "
from janome.tokenizer import Tokenizer
t = Tokenizer()
result = list(t.tokenize('みそ汁にナトリウムが入っているから'))
print('Japanese tokenization successful')
"

# Phase 4: 可視化テスト
python -c "
import matplotlib.pyplot as plt
import seaborn as sns
plt.figure(figsize=(6,4))
sns.barplot(x=[1,2,3], y=[1,2,3])
plt.savefig('outputs/test_plot.png')
print('Visualization test successful')
"
```

## 🔧 設定ファイル生成

### 分析設定ファイル
**config/analysis_config.yaml**:
```yaml
# 分析パラメータ設定
data:
  encoding: "utf-8"
  chunk_size: 1000
  
vocabulary_analysis:
  target_terms:
    - "みそ"
    - "塩" 
    - "食塩"
    - "ナトリウム"
    - "塩化ナトリウム"
  
  scientific_terms:
    basic: ["塩", "食塩"]
    advanced: ["ナトリウム", "塩化ナトリウム", "Na"]
  
  analysis_params:
    significance_level: 0.05
    effect_size_threshold: 0.2
    confidence_interval: 0.95

class_analysis:
  classes: [1.0, 2.0, 3.0, 4.0]
  multiple_comparison: "bonferroni"
  min_sample_size: 5

sentiment_analysis:
  language: "japanese"
  polarity_threshold: 0.1
  interest_keywords:
    - "おもしろい"
    - "すごい" 
    - "きれい"
    - "楽しい"

topic_modeling:
  algorithm: "lda"
  n_topics: 5
  alpha: "auto"
  random_state: 42
  max_iterations: 1000

visualization:
  style: "seaborn-v0_8"
  figure_size: [12, 8]
  font_size: 12
  color_palette: "viridis"
  save_format: "png"
  dpi: 300
```

### パス管理設定
**config/paths.yaml**:
```yaml
# ファイルパス設定
data:
  raw_dir: "data/raw"
  processed_dir: "data/processed" 
  comments: "data/raw/comments.csv"
  q2_before: "data/raw/q2_reasons_before.csv"
  q2_after: "data/raw/q2_reasons_after.csv"

outputs:
  base_dir: "outputs"
  wordclouds: "outputs/wordclouds"
  sentiment: "outputs/sentiment_results"
  topics: "outputs/topic_models"
  statistics: "outputs/statistics"
  visualizations: "outputs/visualizations"

scripts:
  analysis_dir: "scripts/analysis"
  utils_dir: "scripts/utils"
  
logs:
  main_log: "logs/analysis.log"
  error_log: "logs/errors.log"
```

## 📋 インストール完了チェックリスト

### 必須項目
- [ ] Python 3.8+ インストール確認
- [ ] requirements.txt パッケージ導入完了
- [ ] 日本語NLP環境（janome または MeCab）動作確認
- [ ] データファイル3つの存在確認
- [ ] 出力ディレクトリ作成確認

### 推奨項目  
- [ ] 仮想環境の作成・アクティベート
- [ ] 拡張パッケージ（pingouin, plotly等）導入
- [ ] 設定ファイル（YAML）作成
- [ ] 環境検証スクリプト実行
- [ ] テスト実行による動作確認

### 権限問題対応
- [ ] MeCab インストール可能性確認
- [ ] 代替手法（janome）準備確認
- [ ] システム管理者への相談準備（必要時）

## 🆘 サポート・トラブル対応

### 権限問題発生時の連絡事項
```
件名: テキストマイニング環境セットアップ - 権限支援要請

必要な作業:
1. MeCab辞書インストール: sudo apt-get install mecab mecab-ipadic-utf8
2. システムパッケージ更新: sudo apt-get update
3. 環境変数設定の支援

代替手法: 
- janome使用による回避策準備済み
- 分析精度への影響は限定的

緊急度: 中（代替手法により作業継続可能）
```

### エラー報告テンプレート
```markdown
## エラー報告
**発生日時**: 
**作業フェーズ**: 
**エラーメッセージ**: 
```コマンド/エラー内容```
**試行した解決策**: 
**環境情報**: OS、Python version、etc.
```

---

**作成者**: Claude Code Analysis  
**承認**: プロジェクトマネージャー  
**次回更新**: 環境問題発生時または新規要件追加時