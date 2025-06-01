#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ適応型ワードクラウド分析スクリプト
カテゴリ別データ特性を分析してパラメータ最適化戦略を策定
"""

import pandas as pd
import re
from collections import Counter
from janome.tokenizer import Tokenizer
import numpy as np
import json

class DatasetAnalyzer:
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.noise_words = {
            'から', 'です', 'ありがとう', '東京高専', 'へ', 'みなさん', 
            '今日', 'より', 'こと', '一番', 'ます', 'でし', 'まし',
            'が', 'て', 'いる', 'た', 'の', 'に', 'は', 'を', 'で',
            '入っ', 'し', 'なっ', 'っ', 'い', 'ん', 'る', 'れ'
        }
    
    def analyze_by_category(self, df):
        """カテゴリ別データ特性分析"""
        results = {}
        
        for category in df['category'].unique():
            category_df = df[df['category'] == category]
            analysis = self.analyze_category_characteristics(category_df, category)
            results[category] = analysis
        
        return results
    
    def analyze_category_characteristics(self, df, category_name):
        """個別カテゴリの特性分析"""
        texts = df['text'].tolist()
        
        # 基本統計
        total_records = len(texts)
        avg_text_length = np.mean([len(str(text)) for text in texts])
        
        # 語彙分析
        all_words = []
        filtered_words = []
        
        for text in texts:
            text = str(text)
            tokens = self.tokenizer.tokenize(text)
            
            for token in tokens:
                try:
                    word = token.surface
                    if len(word) >= 1:
                        all_words.append(word)
                        
                    # フィルタリング済み語彙
                    if (len(word) >= 2 and 
                        word not in self.noise_words and
                        not re.match(r'^[ぁ-ん]{1}$', word)):
                        filtered_words.append(word)
                        
                except (AttributeError, IndexError):
                    continue
        
        # 語彙統計
        word_freq = Counter(filtered_words)
        unique_words = len(word_freq)
        total_words = len(filtered_words)
        
        # 語彙分布分析
        freq_values = list(word_freq.values())
        vocabulary_density = unique_words / max(total_words, 1)
        
        # 頻度分布
        freq_distribution = {
            'high_freq': len([f for f in freq_values if f >= 10]),  # 10回以上
            'medium_freq': len([f for f in freq_values if 3 <= f < 10]),  # 3-9回
            'low_freq': len([f for f in freq_values if f < 3])  # 1-2回
        }
        
        # トップ語彙
        top_words = dict(word_freq.most_common(20))
        
        return {
            'basic_stats': {
                'records': total_records,
                'avg_text_length': round(avg_text_length, 1),
                'total_words': total_words,
                'unique_words': unique_words,
                'vocabulary_density': round(vocabulary_density, 3)
            },
            'frequency_distribution': freq_distribution,
            'top_words': top_words,
            'recommended_params': self.calculate_optimal_parameters(
                unique_words, freq_distribution, vocabulary_density
            )
        }
    
    def calculate_optimal_parameters(self, unique_words, freq_dist, density):
        """データ特性に基づく最適パラメータ計算"""
        
        # 基本方針
        if unique_words < 30:  # 少語彙（理由説明タイプ）
            params = {
                'max_words': min(unique_words * 2, 50),
                'min_font_size': 28,
                'max_font_size': 200,
                'prefer_horizontal': 0.8,
                'relative_scaling': 0.5,
                'width': 1000,
                'height': 600,
                'strategy': 'compact_focus'
            }
        elif unique_words < 80:  # 中語彙
            params = {
                'max_words': min(unique_words * 1.5, 100),
                'min_font_size': 24,
                'max_font_size': 180,
                'prefer_horizontal': 0.85,
                'relative_scaling': 0.4,
                'width': 1200,
                'height': 700,
                'strategy': 'balanced'
            }
        else:  # 多語彙（感想文タイプ）
            params = {
                'max_words': min(unique_words, 140),
                'min_font_size': 20,
                'max_font_size': 160,
                'prefer_horizontal': 0.9,
                'relative_scaling': 0.3,
                'width': 1400,
                'height': 800,
                'strategy': 'comprehensive'
            }
        
        # 語彙密度による調整
        if density < 0.3:  # 低密度（重複多い）
            params['relative_scaling'] *= 1.2
            params['max_font_size'] = min(params['max_font_size'] * 1.1, 220)
        elif density > 0.7:  # 高密度（多様性高い）
            params['max_words'] = min(params['max_words'] * 1.2, 160)
        
        return params
    
    def generate_optimization_strategy(self, analysis_results):
        """最適化戦略生成"""
        strategies = {}
        
        for category, data in analysis_results.items():
            basic_stats = data['basic_stats']
            params = data['recommended_params']
            
            if basic_stats['unique_words'] < 30:
                strategy_type = "少語彙集中型"
                focus = "核心語彙の強調、コンパクト配置"
                warnings = ["語彙数不足", "単調な表示リスク"]
            elif basic_stats['unique_words'] < 80:
                strategy_type = "中語彙バランス型"
                focus = "重要語彙とサポート語彙のバランス"
                warnings = ["中程度の情報密度"]
            else:
                strategy_type = "多語彙網羅型"
                focus = "多様な語彙の階層的表示"
                warnings = ["情報過多リスク", "小文字の可読性"]
            
            strategies[category] = {
                'type': strategy_type,
                'focus': focus,
                'warnings': warnings,
                'params': params
            }
        
        return strategies

def main():
    """メイン分析実行"""
    print("🔍 **データ適応型ワードクラウド分析**")
    print("=" * 60)
    
    # データ読み込み
    df = pd.read_csv('data/processed/all_text_corpus.csv')
    analyzer = DatasetAnalyzer()
    
    # カテゴリ別分析
    print("📊 カテゴリ別データ特性分析中...")
    analysis_results = analyzer.analyze_by_category(df)
    
    # 結果表示
    for category, data in analysis_results.items():
        print(f"\n{'='*20} {category} {'='*20}")
        stats = data['basic_stats']
        print(f"📝 基本統計:")
        print(f"  レコード数: {stats['records']}件")
        print(f"  平均文字数: {stats['avg_text_length']}文字")
        print(f"  総語数: {stats['total_words']}語")
        print(f"  ユニーク語数: {stats['unique_words']}語")
        print(f"  語彙密度: {stats['vocabulary_density']}")
        
        freq_dist = data['frequency_distribution']
        print(f"\n📈 頻度分布:")
        print(f"  高頻度語(10回+): {freq_dist['high_freq']}語")
        print(f"  中頻度語(3-9回): {freq_dist['medium_freq']}語")
        print(f"  低頻度語(1-2回): {freq_dist['low_freq']}語")
        
        params = data['recommended_params']
        print(f"\n⚙️ 推奨パラメータ:")
        print(f"  最大語数: {params['max_words']}")
        print(f"  フォントサイズ: {params['min_font_size']}-{params['max_font_size']}")
        print(f"  水平優先度: {params['prefer_horizontal']}")
        print(f"  相対スケール: {params['relative_scaling']}")
        print(f"  画像サイズ: {params['width']}x{params['height']}")
        print(f"  戦略: {params['strategy']}")
        
        print(f"\n🏆 トップ語彙 (上位10語):")
        for word, freq in list(data['top_words'].items())[:10]:
            print(f"  {word}: {freq}回")
    
    # 最適化戦略
    print(f"\n{'='*20} 最適化戦略 {'='*20}")
    strategies = analyzer.generate_optimization_strategy(analysis_results)
    
    for category, strategy in strategies.items():
        print(f"\n🎯 {category}:")
        print(f"  戦略タイプ: {strategy['type']}")
        print(f"  重点: {strategy['focus']}")
        print(f"  注意点: {', '.join(strategy['warnings'])}")
    
    # 対策提案
    print(f"\n{'='*20} 対策提案 {'='*20}")
    print("1. 📏 **データ適応型パラメータ**: カテゴリ検出による自動調整")
    print("2. 🎨 **レイアウト最適化**: 語彙数に応じた画像サイズ・密度調整") 
    print("3. 🔄 **動的スケーリング**: 語彙密度による重み付け調整")
    print("4. 📱 **マルチプリセット**: 用途別の最適化済み設定")
    
    # JSON出力
    output_data = {
        'analysis_results': analysis_results,
        'optimization_strategies': strategies
    }
    
    with open('outputs/adaptive_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 分析結果保存: outputs/adaptive_analysis_results.json")

if __name__ == "__main__":
    main()