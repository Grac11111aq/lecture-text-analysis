# 小学校出前授業アンケート テキストマイニングプロジェクト

## プロジェクト概要
小学校における水溶液をテーマとした出前授業後のアンケートから得られたテキストデータを対象とした自然言語処理・テキストマイニングプロジェクトです。

## データについて
- **感想文**: 21件の自由記述による感想
- **Q2理由記述**: 「みそ汁がしょっぱい理由」に関する記述（授業前84件、授業後95件）
- **合計**: 200件のテキストデータ

## 分析目標
- ワードクラウドによる頻出語の可視化
- 感情分析による児童の学習に対する印象変化
- トピックモデリングによる主要テーマの抽出
- 授業前後の表現・理解の質的変化の分析

## プロジェクト構造
```
├── data/
│   ├── raw/                    # 元のテキストデータ
│   │   ├── comments.csv
│   │   ├── q2_reasons_before.csv
│   │   └── q2_reasons_after.csv
│   ├── processed/              # 前処理済みデータ
│   │   ├── all_text_corpus.csv
│   │   └── metadata.json
│   └── context/               # 背景情報
│       └── DATA_CONTEXT.md
├── docs/                      # プロジェクト文書
├── notebooks/                 # Jupyter notebooks
├── scripts/                   # Python scripts
└── outputs/                   # 分析結果
    ├── wordclouds/
    ├── sentiment_results/
    └── topic_models/
```

## 技術スタック（予定）
- **前処理**: MeCab（形態素解析）、janome
- **可視化**: wordcloud, matplotlib, seaborn
- **自然言語処理**: scikit-learn, spaCy
- **トピックモデリング**: gensim (LDA)
- **感情分析**: TextBlob, 日本語感情分析ライブラリ

## セットアップ
```bash
# 依存関係のインストール（今後追加予定）
pip install -r requirements.txt

# MeCabのインストール（システムによる）
# Ubuntu: sudo apt-get install mecab mecab-ipadic-utf8
# macOS: brew install mecab mecab-ipadic
```

## 分析手順
1. **データ前処理** - テキストクリーニング、正規化
2. **形態素解析** - 単語分割、品詞タグ付け
3. **基本統計** - 文字数、単語数の分布
4. **ワードクラウド生成** - 全体、カテゴリ別
5. **感情分析** - ポジティブ/ネガティブ傾向
6. **トピックモデリング** - 主要テーマの抽出
7. **比較分析** - 授業前後の変化

## データの特徴
- **対象**: 小学生（複数クラス）
- **テーマ**: 水溶液の科学実験・理解
- **記述形式**: 自由記述（ひらがな・カタカナ・漢字混在）
- **授業内容**: 具体的な実験体験を含む

## 背景情報
詳細な授業内容と質問項目の設計意図については `data/context/DATA_CONTEXT.md` を参照してください。

---
*このプロジェクトは統計分析プロジェクト `lecture-survey-analysis` から分離されたテキストマイニング特化版です。*