#!/usr/bin/env python3
"""
語彙使用状況デバッグスクリプト
実際にどの語彙がどの程度使われているかを確認
"""

import pandas as pd
import re
from collections import defaultdict, Counter

def extract_vocabularies(text_series, vocabularies):
    """テキストから語彙を抽出"""
    results = defaultdict(list)
    
    for category, words in vocabularies.items():
        for text in text_series:
            if pd.isna(text):
                results[category].append(0)
                continue
                
            text_str = str(text)
            count = 0
            for word in words:
                count += len(re.findall(word, text_str))
            results[category].append(count)
    
    return results

def main():
    print("=== 語彙使用状況デバッグ分析 ===")
    
    # データ読み込み
    before_data = pd.read_csv('data/raw/q2_reasons_before.csv', encoding='utf-8')
    after_data = pd.read_csv('data/raw/q2_reasons_after.csv', encoding='utf-8')
    
    print(f"Before データ: {len(before_data)} 件")
    print(f"After データ: {len(after_data)} 件")
    
    # 語彙定義
    vocabularies = {
        'basic_food': ['みそ', 'みそ汁', 'みそしる'],
        'basic_salt': ['塩', '食塩', '塩分'],
        'scientific': ['ナトリウム', '塩化ナトリウム', 'Na'],
        'advanced': ['Na+', 'NaCl', 'イオン']
    }
    
    # Before データのテキスト例を確認
    print("\n=== Before データのテキスト例 ===")
    for i, text in enumerate(before_data['Q2_MisoSalty_Reason'].head(10)):
        print(f"{i+1}: {text}")
    
    print("\n=== After データのテキスト例 ===")
    for i, text in enumerate(after_data['Q2_MisoSaltyReason'].head(10)):
        print(f"{i+1}: {text}")
    
    # 語彙抽出
    print("\n=== Before データの語彙使用状況 ===")
    before_vocab = extract_vocabularies(before_data['Q2_MisoSalty_Reason'], vocabularies)
    for category, counts in before_vocab.items():
        total = sum(counts)
        usage_rate = (sum([1 for c in counts if c > 0]) / len(counts)) * 100
        print(f"{category}: 総出現数={total}, 使用率={usage_rate:.1f}% ({sum([1 for c in counts if c > 0])}/{len(counts)})")
    
    print("\n=== After データの語彙使用状況 ===")
    after_vocab = extract_vocabularies(after_data['Q2_MisoSaltyReason'], vocabularies)
    for category, counts in after_vocab.items():
        total = sum(counts)
        usage_rate = (sum([1 for c in counts if c > 0]) / len(counts)) * 100
        print(f"{category}: 総出現数={total}, 使用率={usage_rate:.1f}% ({sum([1 for c in counts if c > 0])}/{len(counts)})")
    
    # 全テキストでの語彙検索
    print("\n=== 全テキストでの特定語彙検索 ===")
    all_before_text = ' '.join(before_data['Q2_MisoSalty_Reason'].dropna().astype(str))
    all_after_text = ' '.join(after_data['Q2_MisoSaltyReason'].dropna().astype(str))
    
    target_words = ['ナトリウム', '塩化ナトリウム', 'Na', '塩', '食塩', 'みそ', 'みそ汁']
    
    print("Before データでの語彙出現:")
    for word in target_words:
        count = len(re.findall(word, all_before_text))
        print(f"  {word}: {count}回")
    
    print("After データでの語彙出現:")
    for word in target_words:
        count = len(re.findall(word, all_after_text))
        print(f"  {word}: {count}回")

if __name__ == "__main__":
    main()