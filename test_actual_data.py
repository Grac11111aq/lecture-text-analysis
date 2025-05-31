#!/usr/bin/env python3
"""
実際のプロジェクトデータを使用したワードクラウドテスト
元の分析データと設定ツールの入力データを比較検証
"""

import pandas as pd
import json
from pathlib import Path
import requests

def load_project_data():
    """プロジェクトの実際のデータを読み込み"""
    print("📊 プロジェクトの実際のデータを確認中...")
    
    # 1. 実際の分析データ
    try:
        before_data = pd.read_csv('data/raw/q2_reasons_before.csv', encoding='utf-8')
        after_data = pd.read_csv('data/raw/q2_reasons_after.csv', encoding='utf-8')
        comments_data = pd.read_csv('data/raw/comments.csv', encoding='utf-8')
        
        print("✅ 実際のプロジェクトデータ読み込み成功")
        print(f"   Before: {len(before_data)}件")
        print(f"   After: {len(after_data)}件") 
        print(f"   Comments: {len(comments_data)}件")
        
        return before_data, after_data, comments_data
        
    except Exception as e:
        print(f"❌ プロジェクトデータ読み込みエラー: {e}")
        return None, None, None

def get_webapp_sample_data():
    """Webアプリのサンプルデータを取得"""
    print("\n🌐 Webアプリのサンプルデータを確認中...")
    
    try:
        response = requests.get('http://localhost:5000/api/sample-texts')
        if response.status_code == 200:
            data = response.json()
            print("✅ Webアプリサンプルデータ取得成功")
            return data['texts']
        else:
            print(f"❌ サンプルデータ取得失敗: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ サンプルデータ取得エラー: {e}")
        return None

def analyze_before_after_text(before_data, after_data):
    """Before/Afterデータの実際のテキスト内容を分析"""
    print("\n🔍 Before/Afterデータのテキスト分析...")
    
    # Before データ
    if 'Q2_MisoSalty_Reason' in before_data.columns:
        before_text_col = 'Q2_MisoSalty_Reason'
    else:
        before_text_col = before_data.columns[-1]  # 最後の列を使用
    
    # After データ
    if 'Q2_MisoSaltyReason' in after_data.columns:
        after_text_col = 'Q2_MisoSaltyReason'
    else:
        after_text_col = after_data.columns[-1]  # 最後の列を使用
    
    print(f"📝 Beforeテキスト列: {before_text_col}")
    print(f"📝 Afterテキスト列: {after_text_col}")
    
    # 実際のテキスト例を表示
    print("\n🔤 Before データの実際のテキスト例（最初の10件）:")
    for i, text in enumerate(before_data[before_text_col].head(10)):
        if pd.notna(text):
            print(f"   {i+1}: {text}")
    
    print("\n🔤 After データの実際のテキスト例（最初の10件）:")
    for i, text in enumerate(after_data[after_text_col].head(10)):
        if pd.notna(text):
            print(f"   {i+1}: {text}")
    
    # 全テキストを結合
    before_all_text = ' '.join(before_data[before_text_col].dropna().astype(str))
    after_all_text = ' '.join(after_data[after_text_col].dropna().astype(str))
    
    print(f"\n📊 Beforeテキスト統計:")
    print(f"   総文字数: {len(before_all_text)}")
    print(f"   平均文長: {len(before_all_text) / len(before_data):.1f}文字/件")
    
    print(f"\n📊 Afterテキスト統計:")
    print(f"   総文字数: {len(after_all_text)}")
    print(f"   平均文長: {len(after_all_text) / len(after_data):.1f}文字/件")
    
    return before_all_text, after_all_text

def compare_webapp_vs_project(webapp_data, project_before, project_after):
    """WebアプリのサンプルとプロジェクトデータWを比較"""
    print("\n🔍 Webアプリサンプル vs プロジェクトデータ比較...")
    
    # Webアプリの科学教育サンプル
    science_sample = webapp_data.get('science_education', {}).get('text', '')
    
    print("📝 Webアプリの科学教育サンプル:")
    print(f"   {science_sample[:200]}...")
    print(f"   文字数: {len(science_sample)}")
    
    print(f"\n📝 プロジェクトのBeforeデータ:")
    print(f"   {project_before[:200]}...")
    print(f"   文字数: {len(project_before)}")
    
    print(f"\n📝 プロジェクトのAfterデータ:")
    print(f"   {project_after[:200]}...")
    print(f"   文字数: {len(project_after)}")
    
    # 共通語彙の確認
    common_words = ['ナトリウム', '塩', '実験', '観察', '科学']
    
    print(f"\n🔤 重要語彙の出現確認:")
    for word in common_words:
        webapp_count = science_sample.count(word)
        before_count = project_before.count(word) 
        after_count = project_after.count(word)
        
        print(f"   {word}:")
        print(f"     Webアプリサンプル: {webapp_count}回")
        print(f"     プロジェクトBefore: {before_count}回")
        print(f"     プロジェクトAfter: {after_count}回")

def test_actual_data_wordcloud():
    """実際のプロジェクトデータでワードクラウド生成テスト"""
    print("\n🧪 実際のデータでワードクラウド生成テスト...")
    
    # プロジェクトデータを読み込み
    before_data, after_data, comments_data = load_project_data()
    if before_data is None:
        print("❌ プロジェクトデータが読み込めないため、テストを中断します")
        return
    
    # Before/Afterテキストを結合
    before_text = ' '.join(before_data['Q2_MisoSalty_Reason'].dropna().astype(str))
    after_text = ' '.join(after_data['Q2_MisoSaltyReason'].dropna().astype(str))
    
    # Webアプリでワードクラウド生成テスト
    test_configs = [
        {
            "name": "プロジェクトBeforeデータ",
            "config": {
                "text_source": "custom",
                "custom_text": before_text,
                "font": "IPAexGothic",
                "width": 800,
                "height": 400,
                "max_words": 50,
                "background_color": "white",
                "colormap": "viridis"
            }
        },
        {
            "name": "プロジェクトAfterデータ", 
            "config": {
                "text_source": "custom",
                "custom_text": after_text,
                "font": "IPAexGothic",
                "width": 800,
                "height": 400,
                "max_words": 50,
                "background_color": "white",
                "colormap": "plasma"
            }
        }
    ]
    
    for test_case in test_configs:
        print(f"\n📋 {test_case['name']}でテスト中...")
        try:
            response = requests.post(
                'http://localhost:5000/api/generate',
                json=test_case['config'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"   ✅ 生成成功")
                    print(f"   📏 画像データサイズ: {len(result['image'])}文字")
                else:
                    print(f"   ❌ 生成失敗: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP エラー: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ テストエラー: {e}")

def main():
    """メイン実行"""
    print("🔍 ワードクラウド実装データ検証")
    print("=" * 50)
    
    # 1. プロジェクトデータ読み込み
    before_data, after_data, comments_data = load_project_data()
    
    # 2. Webアプリサンプルデータ取得
    webapp_data = get_webapp_sample_data()
    
    if before_data is not None and after_data is not None:
        # 3. Before/Afterデータ分析
        project_before, project_after = analyze_before_after_text(before_data, after_data)
        
        if webapp_data:
            # 4. データ比較
            compare_webapp_vs_project(webapp_data, project_before, project_after)
        
        # 5. 実際のデータでワードクラウド生成テスト
        test_actual_data_wordcloud()
    
    print("\n" + "=" * 50)
    print("🎯 検証完了")

if __name__ == "__main__":
    main()