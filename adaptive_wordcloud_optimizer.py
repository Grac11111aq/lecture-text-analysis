#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ適応型ワードクラウド最適化システム
カテゴリとデータ特性に基づく動的パラメータ調整
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

class AdaptiveWordCloudOptimizer:
    def __init__(self):
        self.tokenizer = Tokenizer()
        
        # 共通ノイズ語
        self.noise_words = {
            'から', 'です', 'ありがとう', '東京高専', 'へ', 'みなさん', 
            '今日', 'より', 'こと', '一番', 'ます', 'でし', 'まし',
            'が', 'て', 'いる', 'た', 'の', 'に', 'は', 'を', 'で',
            '入っ', 'し', 'なっ', 'っ', 'い', 'ん', 'る', 'れ'
        }
        
        # 科学用語重み（共通）
        self.science_terms = {
            'ナトリウム': 3.0, '塩': 2.5, '食塩': 2.5, '塩分': 2.5,
            '結晶': 2.8, '実験': 2.8, '炎色反応': 3.0, '再結晶': 3.0,
            '成分': 2.0, '塩化ナトリウム': 3.0, 'Na': 3.0, 'NaCl': 3.0
        }
        
        # 感情語重み（共通）
        self.emotion_terms = {
            '印象': 2.0, 'きれい': 2.0, '面白い': 2.2, 'おもしろい': 2.2,
            '楽しい': 2.2, '好き': 2.0, '興味': 2.5, 'びっくり': 2.0, 'すごい': 2.0
        }
        
        # 表記ゆれ統一（共通）
        self.normalization_rules = {
            'みそ汁': 'みそ', 'みそしる': 'みそ', '味噌': 'みそ', '味噌汁': 'みそ',
            'おもしろい': '面白い', 'おもしろく': '面白い', 'おもしろかっ': '面白い',
            'たのしい': '楽しい', 'たのしく': '楽しい', 'たのしかっ': '楽しい',
            'えん分': '塩分', 'エン分': '塩分',
            'とける': '溶ける', 'とけ': '溶ける', 'とかし': '溶ける', '溶かし': '溶ける'
        }
    
    def detect_dataset_type(self, df):
        """データセットタイプの自動検出"""
        category_counts = df['category'].value_counts()
        
        if '感想文' in category_counts and category_counts['感想文'] > 0:
            if len(category_counts) == 1:
                return 'comments_only'
            else:
                return 'mixed'
        elif 'Q2理由_授業前' in category_counts and 'Q2理由_授業後' in category_counts:
            return 'reasoning_only'
        elif 'Q2理由_授業前' in category_counts:
            return 'before_only'
        elif 'Q2理由_授業後' in category_counts:
            return 'after_only'
        else:
            return 'unknown'
    
    def get_adaptive_parameters(self, df, dataset_type):
        """データセットタイプに基づく適応型パラメータ"""
        
        # 語彙数分析
        words = self.extract_and_filter_words(df)
        word_freq = Counter([word for word, category in words])
        unique_words = len(word_freq)
        
        # パラメータセット定義
        if dataset_type == 'comments_only':
            # 感想文専用：多語彙網羅型
            params = {
                'max_words': min(unique_words, 140),
                'min_font_size': 20,
                'max_font_size': 160,
                'prefer_horizontal': 0.9,
                'relative_scaling': 0.3,
                'width': 1400,
                'height': 800,
                'colormap': 'viridis',
                'background_color': '#f8f8f8'
            }
        elif dataset_type in ['reasoning_only', 'before_only', 'after_only']:
            # 理由説明専用：少語彙集中型
            params = {
                'max_words': min(unique_words, 50),  # 大幅削減
                'min_font_size': 32,  # 大型フォント
                'max_font_size': 220,  # 超大型フォント
                'prefer_horizontal': 0.75,  # 縦書き許容
                'relative_scaling': 0.6,  # 強いスケーリング
                'width': 1000,  # コンパクト幅
                'height': 600,  # コンパクト高さ
                'colormap': 'plasma',
                'background_color': '#f5f5f5'
            }
        else:  # mixed
            # 統合型：バランス調整
            params = {
                'max_words': min(unique_words, 100),
                'min_font_size': 24,
                'max_font_size': 180,
                'prefer_horizontal': 0.85,
                'relative_scaling': 0.4,
                'width': 1200,
                'height': 700,
                'colormap': 'coolwarm',
                'background_color': '#f8f8f8'
            }
        
        return params, unique_words
    
    def extract_and_filter_words(self, df):
        """語彙抽出・フィルタリング（共通処理）"""
        filtered_words = []
        
        for idx, row in df.iterrows():
            text = str(row['text'])
            category = row['category']
            
            # 前処理
            text = re.sub(r'[0-9０-９]', '', text)
            text = re.sub(r'[，。！？・「」『』（）()]', '', text)
            
            # 形態素解析
            tokens = self.tokenizer.tokenize(text)
            for token in tokens:
                try:
                    word = token.surface
                    
                    # フィルタリング
                    if (len(word) >= 2 and 
                        word not in self.noise_words and
                        not re.match(r'^[ぁ-ん]{1}$', word)):
                        
                        # 表記ゆれ統一
                        if word in self.normalization_rules:
                            word = self.normalization_rules[word]
                        
                        filtered_words.append((word, category))
                        
                except (AttributeError, IndexError):
                    continue
        
        return filtered_words
    
    def calculate_weighted_frequencies(self, words):
        """重み付き頻度計算（共通処理）"""
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
    
    def generate_adaptive_wordcloud(self, df, title_suffix=""):
        """適応型ワードクラウド生成"""
        
        # データセットタイプ検出
        dataset_type = self.detect_dataset_type(df)
        print(f"🔍 検出されたデータセットタイプ: {dataset_type}")
        
        # 適応型パラメータ取得
        params, unique_words = self.get_adaptive_parameters(df, dataset_type)
        print(f"📊 語彙数: {unique_words}語")
        print(f"⚙️ 適用パラメータ: max_words={params['max_words']}, font_size={params['min_font_size']}-{params['max_font_size']}")
        
        # 語彙処理
        words = self.extract_and_filter_words(df)
        weighted_freq = self.calculate_weighted_frequencies(words)
        
        # フォント設定
        font_path = 'fonts/ipaexg.ttf'
        
        # ワードクラウド生成
        wordcloud = WordCloud(
            font_path=font_path,
            width=params['width'],
            height=params['height'],
            background_color=params['background_color'],
            max_words=params['max_words'],
            min_font_size=params['min_font_size'],
            max_font_size=params['max_font_size'],
            prefer_horizontal=params['prefer_horizontal'],
            relative_scaling=params['relative_scaling'],
            colormap=params['colormap']
        )
        
        if weighted_freq:
            wordcloud.generate_from_frequencies(weighted_freq)
            
            # タイトル設定
            title = f"適応型ワードクラウド ({dataset_type}){title_suffix}"
            
            # 可視化
            plt.figure(figsize=(params['width']/100, params['height']/100))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.tight_layout()
            
            return wordcloud, weighted_freq, params, dataset_type
        else:
            print("⚠️ 有効な語彙が見つかりませんでした")
            return None, {}, {}, dataset_type

def generate_comparison_wordclouds():
    """比較用ワードクラウド生成"""
    print("🎨 **適応型ワードクラウド比較生成**")
    print("=" * 60)
    
    # データ読み込み
    df = pd.read_csv('data/processed/all_text_corpus.csv')
    optimizer = AdaptiveWordCloudOptimizer()
    
    # カテゴリ別生成
    categories = {
        '感想文': df[df['category'] == '感想文'],
        '授業前理由': df[df['category'] == 'Q2理由_授業前'],
        '授業後理由': df[df['category'] == 'Q2理由_授業後'],
        '全データ': df
    }
    
    results = {}
    
    for name, data in categories.items():
        print(f"\n{'='*20} {name} ワードクラウド生成 {'='*20}")
        
        wordcloud, frequencies, params, dataset_type = optimizer.generate_adaptive_wordcloud(
            data, title_suffix=f" - {name}"
        )
        
        if wordcloud:
            # 保存
            output_path = f'outputs/wordclouds/adaptive_{name.replace("理由", "reason")}.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"💾 保存完了: {output_path}")
            
            # トップ語彙表示
            print(f"🏆 トップ語彙 (上位10語):")
            for word, weight in sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {word}: {weight:.1f}")
            
            results[name] = {
                'wordcloud': wordcloud,
                'frequencies': frequencies,
                'parameters': params,
                'dataset_type': dataset_type
            }
            
            plt.close()  # メモリ節約
    
    return results

def main():
    """メイン実行"""
    results = generate_comparison_wordclouds()
    
    print(f"\n✅ **適応型最適化完了**")
    print("🎯 **効果的な対策実装**:")
    print("  1. データセットタイプ自動検出")
    print("  2. 語彙数に応じた動的パラメータ調整")
    print("  3. カテゴリ最適化済みレイアウト")
    print("  4. 理由説明用コンパクト設計")

if __name__ == "__main__":
    main()