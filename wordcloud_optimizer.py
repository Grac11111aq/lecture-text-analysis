#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ワードクラウド最適化スクリプト
教育データの語彙を高度に処理して質の高いワードクラウドを生成
"""

import pandas as pd
import re
from collections import Counter
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAGothic', 'VL Gothic', 'Noto Sans CJK JP']

class WordCloudOptimizer:
    def __init__(self):
        self.tokenizer = Tokenizer()
        
        # 高頻度ノイズ語（分析結果に基づく）
        self.noise_words = {
            'から', 'です', 'ありがとう', '東京高専', 'へ', 'みなさん', 
            '今日', 'より', 'こと', '一番', 'ます', 'でし', 'まし',
            'が', 'て', 'いる', 'た', 'の', 'に', 'は', 'を', 'で',
            '入っ', 'し', 'なっ', 'っ', 'い', 'ん', 'る', 'れ'
        }
        
        # 科学用語（優先表示・重み増加）
        self.science_terms = {
            'ナトリウム': 3.0,
            '塩': 2.5, 
            '食塩': 2.5,
            '塩分': 2.5,
            '結晶': 2.8,
            '実験': 2.8,
            '炎色反応': 3.0,
            '再結晶': 3.0,
            '成分': 2.0,
            '塩化ナトリウム': 3.0,
            'Na': 3.0,
            'NaCl': 3.0
        }
        
        # 感情・評価語（教育効果表現）
        self.emotion_terms = {
            '印象': 2.0,
            'きれい': 2.0,
            '面白い': 2.2,
            'おもしろい': 2.2,
            '楽しい': 2.2,
            '好き': 2.0,
            '興味': 2.5,
            'びっくり': 2.0,
            'すごい': 2.0
        }
        
        # 表記ゆれ統一ルール
        self.normalization_rules = {
            # みそ系統一
            'みそ汁': 'みそ',
            'みそしる': 'みそ',
            '味噌': 'みそ',
            '味噌汁': 'みそ',
            
            # 面白い系統一
            'おもしろい': '面白い',
            'おもしろく': '面白い',
            'おもしろかっ': '面白い',
            
            # 楽しい系統一
            'たのしい': '楽しい',
            'たのしく': '楽しい',
            'たのしかっ': '楽しい',
            
            # 塩系統一（最重要）
            'えん分': '塩分',
            'エン分': '塩分',
            
            # 溶ける系統一
            'とける': '溶ける',
            'とけ': '溶ける',
            'とかし': '溶ける',
            '溶かし': '溶ける'
        }
        
        # 最小語長（1文字語除外）
        self.min_word_length = 2
        
    def preprocess_text(self, text):
        """テキスト前処理"""
        text = str(text)
        # 数字・記号除去
        text = re.sub(r'[0-9０-９]', '', text)
        text = re.sub(r'[，。！？・「」『』（）()]', '', text)
        return text
    
    def extract_and_filter_words(self, df):
        """語彙抽出・フィルタリング・正規化"""
        filtered_words = []
        
        for idx, row in df.iterrows():
            text = self.preprocess_text(row['text'])
            category = row['category']
            
            # 形態素解析
            tokens = self.tokenizer.tokenize(text)
            for token in tokens:
                try:
                    word = token.surface
                    
                    # 基本フィルタリング
                    if (len(word) >= self.min_word_length and 
                        word not in self.noise_words and
                        not re.match(r'^[ぁ-ん]{1}$', word)):  # ひらがな1文字除外
                        
                        # 表記ゆれ統一
                        if word in self.normalization_rules:
                            word = self.normalization_rules[word]
                        
                        filtered_words.append((word, category))
                        
                except (AttributeError, IndexError):
                    continue
        
        return filtered_words
    
    def calculate_word_weights(self, words):
        """語彙重み計算（教育的価値反映）"""
        word_freq = Counter([word for word, category in words])
        weighted_freq = {}
        
        for word, freq in word_freq.items():
            base_weight = freq
            
            # 科学用語重み増加
            if word in self.science_terms:
                weight = base_weight * self.science_terms[word]
            # 感情語重み増加
            elif word in self.emotion_terms:
                weight = base_weight * self.emotion_terms[word]
            else:
                weight = base_weight
            
            weighted_freq[word] = weight
        
        return weighted_freq
    
    def generate_optimized_wordcloud(self, df, title="最適化ワードクラウド", 
                                   width=1200, height=800):
        """最適化ワードクラウド生成"""
        # 語彙処理
        words = self.extract_and_filter_words(df)
        weighted_freq = self.calculate_word_weights(words)
        
        # フォント設定
        font_path = 'fonts/ipaexg.ttf'
        
        # ワードクラウド設定
        wordcloud = WordCloud(
            font_path=font_path,
            width=width,
            height=height,
            background_color='#f8f8f8',
            max_words=120,
            min_font_size=20,
            max_font_size=180,
            prefer_horizontal=0.9,
            relative_scaling=0.3,
            colormap='plasma'  # 既存のカラーマップを使用
        )
        
        # ワードクラウド生成
        if weighted_freq:
            wordcloud.generate_from_frequencies(weighted_freq)
            
            # 可視化
            plt.figure(figsize=(15, 10))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title(title, fontsize=20, fontweight='bold', pad=20)
            plt.tight_layout()
            
            return wordcloud, weighted_freq
        else:
            print("⚠️ 有効な語彙が見つかりませんでした")
            return None, {}
    
    def compare_before_after(self, df):
        """改善前後の比較分析"""
        print("🔍 **改善前後比較分析**")
        print("=" * 50)
        
        # 原文分析
        original_words = []
        for text in df['text']:
            tokens = self.tokenizer.tokenize(str(text))
            for token in tokens:
                try:
                    word = token.surface
                    if len(word) >= 1:
                        original_words.append(word)
                except:
                    continue
        
        # 最適化後分析
        optimized_words = self.extract_and_filter_words(df)
        optimized_word_list = [word for word, category in optimized_words]
        
        original_freq = Counter(original_words)
        optimized_freq = Counter(optimized_word_list)
        
        print(f"📊 語彙数変化:")
        print(f"  原文: {len(original_freq)}語 (総{len(original_words)}語)")
        print(f"  最適化後: {len(optimized_freq)}語 (総{len(optimized_word_list)}語)")
        print(f"  ノイズ除去率: {(1 - len(optimized_word_list)/len(original_words))*100:.1f}%")
        
        print(f"\n🎯 科学用語頻度変化:")
        for term in ['ナトリウム', '塩', '結晶', '実験']:
            orig_count = original_freq.get(term, 0)
            opt_count = optimized_freq.get(term, 0)
            print(f"  {term}: {orig_count} → {opt_count}回")
        
        print(f"\n🗑️ 除去されたノイズ語（上位10語）:")
        removed_words = set(original_freq.keys()) - set(optimized_freq.keys())
        removed_freq = {word: original_freq[word] for word in removed_words}
        for word, freq in sorted(removed_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {word}: {freq}回")

def main():
    """メイン実行"""
    print("🎨 **ワードクラウド最適化実行**")
    print("=" * 50)
    
    # データ読み込み
    df = pd.read_csv('data/processed/all_text_corpus.csv')
    print(f"📊 データ: {len(df)}件")
    
    # オプティマイザー初期化
    optimizer = WordCloudOptimizer()
    
    # 比較分析
    optimizer.compare_before_after(df)
    
    # 最適化ワードクラウド生成
    print(f"\n🎨 最適化ワードクラウド生成中...")
    wordcloud, weighted_freq = optimizer.generate_optimized_wordcloud(
        df, title="最適化されたワードクラウド（教育効果重視）"
    )
    
    if wordcloud:
        # 保存
        output_path = 'outputs/wordclouds/optimized_wordcloud.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"💾 保存完了: {output_path}")
        
        # 重要語彙表示
        print(f"\n⭐ **重要語彙ランキング（重み付き）**")
        for word, weight in sorted(weighted_freq.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  {word}: {weight:.1f}")
        
        plt.show()
    
    print("\n✅ **最適化完了**")

if __name__ == "__main__":
    main()