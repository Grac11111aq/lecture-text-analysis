#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ワードクラウド品質改善のための語彙分析スクリプト
教育データの語彙を分類・正規化して質の高いワードクラウドを生成
"""

import pandas as pd
import re
from collections import Counter, defaultdict
from janome.tokenizer import Tokenizer
import json

def load_and_analyze_data():
    """データ読み込みと基本統計"""
    df = pd.read_csv('data/processed/all_text_corpus.csv')
    print(f"📊 データ概要: {len(df)}件")
    print(f"カテゴリ分布: {df['category'].value_counts().to_dict()}")
    print(f"クラス分布: {df['class'].value_counts().to_dict()}")
    return df

def tokenize_and_analyze(df):
    """形態素解析と語彙分析"""
    tokenizer = Tokenizer()
    
    all_words = []
    word_categories = defaultdict(list)
    word_contexts = defaultdict(list)
    
    for idx, row in df.iterrows():
        text = str(row['text'])
        category = row['category']
        
        # 形態素解析
        tokens = tokenizer.tokenize(text)
        for token in tokens:
            try:
                word = token.surface
                # features が None の場合のエラーハンドリング
                if hasattr(token, 'features') and token.features:
                    pos = token.features.split(',')[0]  # 品詞
                else:
                    pos = 'Unknown'
                
                # 基本フィルタリング
                if len(word) >= 1 and word not in ['、', '。', '？', '！']:
                    all_words.append(word)
                    word_categories[category].append(word)
                    word_contexts[word].append({
                        'category': category,
                        'class': row['class'],
                        'pos': pos,
                        'context': text[:30] + '...' if len(text) > 30 else text
                    })
            except (AttributeError, IndexError) as e:
                # トークン処理でエラーが発生した場合はスキップ
                continue
    
    return all_words, word_categories, word_contexts

def classify_vocabulary(all_words, word_contexts):
    """語彙を教育的価値で分類"""
    word_freq = Counter(all_words)
    
    # 教育的語彙分類
    scientific_terms = []      # 科学用語
    educational_terms = []     # 教育関連語
    emotion_terms = []        # 感情語
    noise_terms = []          # ノイズ語
    greeting_terms = []       # 挨拶語
    
    # 科学用語パターン
    science_patterns = [
        r'ナトリウム', r'塩化ナトリウム', r'Na\+?', r'NaCl',
        r'塩', r'食塩', r'塩分',
        r'炎色反応', r'再結晶', r'実験', r'結晶',
        r'バリウム', r'カルシウム', r'ストロンチウム',
        r'水よう液', r'とける', r'溶ける', r'成分'
    ]
    
    # 感情・評価語パターン  
    emotion_patterns = [
        r'面白い', r'おもしろい', r'楽しい', r'たのしい',
        r'すごい', r'きれい', r'印象', r'びっくり',
        r'好き', r'興味', r'感動'
    ]
    
    # ノイズ語パターン
    noise_patterns = [
        r'ありがとう', r'より', r'へ', r'から', r'です', r'ます',
        r'東京高専', r'みなさん', r'今日', r'一番',
        r'こと', r'もの', r'時', r'所', r'場所'
    ]
    
    # 挨拶語パターン
    greeting_patterns = [
        r'ありがとう', r'お疲れ', r'よろしく',
        r'こんにちは', r'さようなら'
    ]
    
    for word, freq in word_freq.most_common():
        classified = False
        
        # 科学用語判定
        for pattern in science_patterns:
            if re.search(pattern, word):
                scientific_terms.append((word, freq))
                classified = True
                break
        
        if not classified:
            # 感情語判定
            for pattern in emotion_patterns:
                if re.search(pattern, word):
                    emotion_terms.append((word, freq))
                    classified = True
                    break
        
        if not classified:
            # ノイズ語判定
            for pattern in noise_patterns:
                if re.search(pattern, word):
                    noise_terms.append((word, freq))
                    classified = True
                    break
        
        if not classified:
            # 挨拶語判定
            for pattern in greeting_patterns:
                if re.search(pattern, word):
                    greeting_terms.append((word, freq))
                    classified = True
                    break
        
        if not classified:
            # その他は教育関連として分類
            educational_terms.append((word, freq))
    
    return {
        'scientific': scientific_terms,
        'educational': educational_terms,
        'emotion': emotion_terms,
        'noise': noise_terms,
        'greeting': greeting_terms
    }

def find_normalization_candidates(all_words):
    """表記ゆれ候補を検出"""
    word_freq = Counter(all_words)
    
    # 表記ゆれ候補グループ
    normalization_groups = {
        'みそ系': ['みそ', 'みそ汁', 'みそしる', '味噌', '味噌汁'],
        '面白い系': ['面白い', 'おもしろい', 'おもしろく'],
        '楽しい系': ['楽しい', 'たのしい', 'たのしく'],
        '塩系': ['塩', '食塩', '塩分', 'えん分'],
        '科学系': ['ナトリウム', '塩化ナトリウム', 'Na', 'NaCl'],
        '実験系': ['実験', '炎色反応', '再結晶', '結晶'],
        '溶ける系': ['とける', '溶ける', 'とけた', '溶けた']
    }
    
    detected_groups = {}
    for group_name, candidates in normalization_groups.items():
        found_words = []
        for word in candidates:
            if word in word_freq:
                found_words.append((word, word_freq[word]))
        if found_words:
            detected_groups[group_name] = found_words
    
    return detected_groups

def analyze_educational_progression():
    """授業前後の語彙変化分析（教育効果測定）"""
    df = pd.read_csv('data/processed/all_text_corpus.csv')
    
    before_texts = df[df['category'] == 'Q2理由_授業前']['text'].tolist()
    after_texts = df[df['category'] == 'Q2理由_授業後']['text'].tolist()
    
    tokenizer = Tokenizer()
    
    def extract_key_terms(texts):
        terms = []
        for text in texts:
            tokens = tokenizer.tokenize(str(text))
            for token in tokens:
                word = token.surface
                if word in ['塩', 'ナトリウム', '食塩', '塩化ナトリウム', 'Na']:
                    terms.append(word)
        return Counter(terms)
    
    before_terms = extract_key_terms(before_texts)
    after_terms = extract_key_terms(after_texts)
    
    print("\n🎯 **教育効果分析（核心語彙の変化）**")
    print("授業前:", dict(before_terms))
    print("授業後:", dict(after_terms))
    
    # ナトリウム使用率
    before_total = sum(before_terms.values())
    after_total = sum(after_terms.values())
    
    if before_total > 0:
        before_na_rate = before_terms.get('ナトリウム', 0) / before_total * 100
    else:
        before_na_rate = 0
        
    if after_total > 0:
        after_na_rate = after_terms.get('ナトリウム', 0) / after_total * 100
    else:
        after_na_rate = 0
    
    print(f"ナトリウム使用率: {before_na_rate:.1f}% → {after_na_rate:.1f}%")
    print(f"教育効果: +{after_na_rate - before_na_rate:.1f}ポイント")

def main():
    """メイン分析実行"""
    print("🔍 **ワードクラウド改善のための語彙分析**")
    print("=" * 50)
    
    # データ読み込み
    df = load_and_analyze_data()
    
    # 形態素解析
    print("\n📝 形態素解析実行中...")
    all_words, word_categories, word_contexts = tokenize_and_analyze(df)
    
    # 語彙分類
    print("\n🏷️ 語彙分類実行中...")
    vocab_classification = classify_vocabulary(all_words, word_contexts)
    
    # 結果表示
    print("\n📊 **語彙分類結果**")
    for category, words in vocab_classification.items():
        print(f"\n{category.upper()}語彙 ({len(words)}語):")
        for word, freq in sorted(words, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {word}: {freq}回")
    
    # 表記ゆれ分析
    print("\n🔄 **表記ゆれ分析**")
    normalization_groups = find_normalization_candidates(all_words)
    for group_name, words in normalization_groups.items():
        print(f"\n{group_name}:")
        for word, freq in words:
            print(f"  {word}: {freq}回")
    
    # 教育効果分析
    analyze_educational_progression()
    
    # 改善提案
    print("\n💡 **改善提案**")
    print("1. ノイズ語除外:", [w[0] for w in vocab_classification['noise'][:5]])
    print("2. 挨拶語除外:", [w[0] for w in vocab_classification['greeting'][:3]])
    print("3. 科学用語強調:", [w[0] for w in vocab_classification['scientific'][:5]])
    print("4. 表記統一必要:", list(normalization_groups.keys()))

if __name__ == "__main__":
    main()