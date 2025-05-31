# 東京高専出前授業テキストマイニング実装ワークフロー

**プロジェクト**: 小学校出前授業アンケート分析による教育効果測定  
**作成日**: 2025-05-31  
**更新日**: 2025-05-31  
**ステータス**: Phase 1 - 計画策定完了  

## 📋 プロジェクト概要

### 分析対象データ
- **comments.csv**: 児童感想文 (21件)
- **q2_reasons_before.csv**: 授業前理由説明 (84件) 
- **q2_reasons_after.csv**: 授業後理由説明 (95件)
- **クラス情報**: 4クラス (1.0, 2.0, 3.0, 4.0)

### 主要分析目標
1. **科学語彙習得効果**: 「塩」→「ナトリウム」変化の定量化
2. **クラス間差異分析**: 4クラスの教育効果比較
3. **感情・興味変化**: 実験への反応と学習意欲測定
4. **教育手法評価**: 炎色反応・再結晶実験の効果検証

## 🚀 実装フェーズ別詳細計画

### Phase 1: 環境セットアップ・基盤構築 (Week 1)

#### 1.1 Python環境セットアップ
```bash
# 実行場所: プロジェクトルート
pip install -r requirements.txt

# 日本語NLP追加パッケージ (MeCab関連で権限問題の可能性)
pip install fugashi unidic-lite

# 統計・可視化強化
pip install plotly kaleido pingouin
```

**潜在的権限問題**:
- MeCab辞書インストール: `sudo apt-get install mecab mecab-ipadic-utf8`
- システムレベルの辞書更新が必要な場合は手動対応要請

#### 1.2 ディレクトリ構造最終化
```
scripts/
├── setup/
│   ├── install_dependencies.py     # 依存関係自動インストール
│   └── validate_environment.py     # 環境検証スクリプト
├── utils/
│   ├── data_loader.py             # データ読み込み統一化
│   ├── text_preprocessor.py       # テキスト前処理ユーティリティ
│   └── visualization_utils.py     # 可視化共通機能
└── analysis/
    ├── 01_data_exploration.py     # 探索的データ分析
    ├── 02_vocabulary_analysis.py  # 語彙変化分析
    ├── 03_class_comparison.py     # クラス間比較分析
    ├── 04_sentiment_analysis.py   # 感情・興味分析
    ├── 05_topic_modeling.py       # トピックモデリング
    └── 06_statistical_testing.py  # 統計的検定・効果量
```

#### 1.3 設定ファイル作成
- `config/analysis_config.yaml`: 分析パラメータ集約
- `config/paths.yaml`: ファイルパス管理
- `config/visualization_config.yaml`: 図表スタイル設定

### Phase 2: データ処理・探索分析 (Week 1-2)

#### 2.1 データ統合・前処理スクリプト
**scripts/utils/data_loader.py**
```python
# 主要機能:
- 3つのCSVファイルの統一的読み込み
- クラス情報の正規化・検証
- 欠損値・異常値の検出・処理
- 統合データフレームの生成
```

**scripts/utils/text_preprocessor.py**
```python
# 主要機能:
- 日本語テキストの正規化（表記ゆれ統一）
- 形態素解析（janome/MeCab選択可能）
- ストップワード除去・語幹抽出
- 科学語彙の分類・タグ付け
```

#### 2.2 探索的データ分析
**scripts/analysis/01_data_exploration.py**
```python
# 分析内容:
- 基本統計量（文字数、語数、クラス分布）
- Before/After サンプルサイズ分析
- テキスト品質評価（空白回答、意味不明回答の特定）
- クラス別特徴の初期観察

# 出力:
- outputs/exploration/basic_statistics.json
- outputs/exploration/data_quality_report.html
- outputs/exploration/sample_distribution.png
```

### Phase 3: 核心分析実装 (Week 2-3)

#### 3.1 語彙変化分析システム
**scripts/analysis/02_vocabulary_analysis.py**
```python
# 核心機能:
class VocabularyAnalyzer:
    def extract_scientific_terms(self, text_data):
        """科学語彙の抽出・分類"""
        # 対象語彙: 「みそ」「塩」「食塩」「ナトリウム」「塩化ナトリウム」
        
    def calculate_usage_rates(self, before_data, after_data):
        """使用率の計算・比較"""
        
    def statistical_testing(self, before_rates, after_rates):
        """統計的検定・効果量算出"""
        # Mann-Whitney U検定
        # Cohen's d効果量
        # 95%信頼区間
        
    def class_comparison(self, data_by_class):
        """クラス間比較分析"""
        # Kruskal-Wallis検定
        # 事後検定（Dunn検定）
        # クラス別効果量

# 出力ファイル:
- outputs/vocabulary/term_usage_rates.csv
- outputs/vocabulary/statistical_results.json
- outputs/vocabulary/class_comparison_results.json
- outputs/vocabulary/effect_size_comparison.png
```

#### 3.2 クラス間比較分析
**scripts/analysis/03_class_comparison.py**
```python
# 分析機能:
class ClassComparisonAnalyzer:
    def profile_classes(self, data):
        """各クラスの特性プロファイリング"""
        
    def interaction_analysis(self, data):
        """時期×クラス交互作用分析"""
        # 2元配置分散分析
        
    def success_factor_analysis(self, data):
        """成功要因の特定"""
        # 最高効果クラスの詳細分析
        
    def recommendation_generator(self, analysis_results):
        """クラス別改善提案生成"""

# 出力ファイル:
- outputs/class_analysis/class_profiles.json
- outputs/class_analysis/interaction_effects.json
- outputs/class_analysis/success_factors.md
- outputs/class_analysis/class_comparison_heatmap.png
```

#### 3.3 感情・興味分析
**scripts/analysis/04_sentiment_analysis.py**
```python
# 分析機能:
class SentimentInterestAnalyzer:
    def sentiment_analysis(self, comments_data):
        """感情極性分析"""
        # TextBlob + 日本語対応調整
        
    def interest_vocabulary_analysis(self, comments_data):
        """興味関心語彙の抽出・分析"""
        # 「おもしろい」「すごい」「きれい」等の定量化
        
    def experiment_feedback_analysis(self, comments_data):
        """実験別フィードバック分析"""
        # 「炎色反応」「再結晶」言及の分析
        
    def wordcloud_generation(self, text_data, class_info):
        """ワードクラウド生成（全体・クラス別）"""

# 出力ファイル:
- outputs/sentiment_results/emotion_distribution.png
- outputs/sentiment_results/interest_keywords.csv
- outputs/sentiment_results/experiment_feedback.json
- outputs/wordclouds/overall_wordcloud.png
- outputs/wordclouds/class_1_wordcloud.png (x4クラス)
```

### Phase 4: 高度分析・統合 (Week 3-4)

#### 4.1 トピックモデリング
**scripts/analysis/05_topic_modeling.py**
```python
class TopicModelingAnalyzer:
    def lda_analysis(self, text_data, n_topics=5):
        """LDAトピックモデリング"""
        
    def topic_evolution_analysis(self, before_topics, after_topics):
        """トピック分布の変化分析"""
        
    def concept_network_analysis(self, text_data):
        """概念ネットワーク分析"""
        # 共起語分析・ネットワーク可視化

# 出力ファイル:
- outputs/topic_models/lda_model.pkl
- outputs/topic_models/topic_distribution.json
- outputs/topic_models/topic_evolution.png
- outputs/topic_models/concept_network.png
```

#### 4.2 統計的検定・効果量分析
**scripts/analysis/06_statistical_testing.py**
```python
class StatisticalTestingAnalyzer:
    def comprehensive_testing(self, data):
        """包括的統計検定"""
        # 主効果・交互作用・事後検定
        
    def effect_size_analysis(self, data):
        """効果量の詳細分析"""
        # Cohen's d, Hedge's g, Cliff's delta
        
    def power_analysis(self, data):
        """検定力分析"""
        
    def confidence_intervals(self, data):
        """信頼区間の算出"""

# 出力ファイル:
- outputs/statistics/comprehensive_test_results.json
- outputs/statistics/effect_sizes.csv
- outputs/statistics/power_analysis.json
- outputs/statistics/confidence_intervals.png
```

## 📊 実行スケジュール・TODO管理

### Week 1: 環境構築・基盤整備

#### Day 1-2: セットアップ
- [ ] Python環境・依存関係インストール
- [ ] MeCab/辞書セットアップ（権限問題時は要相談）
- [ ] 設定ファイル作成
- [ ] データ読み込み・前処理ユーティリティ開発

#### Day 3-4: 探索分析
- [ ] 基本統計量算出スクリプト実行
- [ ] データ品質確認・クリーニング実施
- [ ] クラス分布・特徴の初期把握

#### Day 5-7: 核心分析準備
- [ ] 語彙分析システム実装
- [ ] 統計検定フレームワーク構築
- [ ] 可視化テンプレート作成

### Week 2: 核心分析実行

#### Day 8-10: 語彙変化分析
- [ ] 科学語彙抽出・分類実行
- [ ] Before/After使用率比較
- [ ] 統計的検定・効果量算出
- [ ] クラス間比較分析

#### Day 11-12: 感情・興味分析
- [ ] 感想文の感情極性分析
- [ ] 興味語彙・実験フィードバック分析
- [ ] ワードクラウド生成

#### Day 13-14: 中間結果統合
- [ ] 主要発見事項の整理
- [ ] 可視化図表の品質確認
- [ ] 次週分析項目の優先順位調整

### Week 3: 高度分析・検証

#### Day 15-17: トピックモデリング
- [ ] LDA実行・パラメータ調整
- [ ] トピック分布変化分析
- [ ] 概念ネットワーク構築

#### Day 18-19: 統計的検証
- [ ] 包括的検定実施
- [ ] 検定力・信頼性分析
- [ ] 結果の頑健性確認

#### Day 20-21: 品質保証
- [ ] 全分析結果の相互検証
- [ ] 外れ値・異常値の再確認
- [ ] 解釈妥当性の検討

### Week 4: 統合・報告書作成

#### Day 22-24: 結果統合
- [ ] 全分析結果の総合解釈
- [ ] ステークホルダー別要点抽出
- [ ] 教育的示唆の整理

#### Day 25-28: 報告書作成
- [ ] 技術報告書作成
- [ ] エグゼクティブサマリー作成
- [ ] 教育実践ガイド作成
- [ ] プロジェクト成果報告作成

## 🔧 技術的実装詳細

### 設定管理システム
**config/analysis_config.yaml**
```yaml
# 分析パラメータ
vocabulary_analysis:
  target_terms: ["みそ", "塩", "食塩", "ナトリウム", "塩化ナトリウム"]
  significance_level: 0.05
  effect_size_threshold: 0.2

class_analysis:
  classes: [1.0, 2.0, 3.0, 4.0]
  multiple_comparison_method: "bonferroni"
  
topic_modeling:
  n_topics: 5
  random_state: 42
  iterations: 1000

visualization:
  figure_size: [12, 8]
  color_palette: "viridis"
  font_family: "DejaVu Sans"
```

### エラーハンドリング・ログ管理
```python
# scripts/utils/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level="INFO"):
    """統一ログ設定"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "analysis.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

### データベース化（将来拡張）
```python
# scripts/utils/database_manager.py
# SQLite/PostgreSQL対応のデータ永続化
# 分析結果の版管理・比較機能
```

## 📋 タスク管理・進捗追跡

### 進捗トラッキング
- **マスターTODO**: `docs/tasks/master_todo.md`
- **週次進捗**: `docs/tasks/weekly_progress/`
- **完了アーカイブ**: `docs/tasks/completed/`

### 品質保証チェックリスト
- [ ] 全スクリプトの単体テスト実施
- [ ] データ処理の再現可能性確認
- [ ] 統計的前提条件の検証
- [ ] 可視化の品質・一貫性確認
- [ ] 文書の整合性・完全性確認

### リスク管理
**高リスク項目**:
1. **MeCab権限問題**: 代替手法（janome）準備済み
2. **メモリ不足**: バッチ処理・チャンク化対応
3. **統計的前提違反**: ノンパラメトリック検定準備
4. **解釈の主観性**: 複数手法による三角測定

## 🎯 成功基準・完了条件

### 技術的成功基準
- [ ] 全分析スクリプト正常実行
- [ ] 統計的に有意な結果の検出（p < 0.05）
- [ ] 実質的意味のある効果量（Cohen's d > 0.2）
- [ ] 4ステークホルダー向け報告書完成

### 教育的成功基準
- [ ] 科学語彙習得の定量的証明
- [ ] クラス間差異の具体的特定
- [ ] 実践的改善提案の提示
- [ ] 東京高専プロジェクト価値の可視化

---

**次回更新予定**: Phase 1完了時（Week 1終了）  
**アーカイブ方針**: 各フェーズ完了時にバージョン管理し、`docs/workflows/archive/`に保存