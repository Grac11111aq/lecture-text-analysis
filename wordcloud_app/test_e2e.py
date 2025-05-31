#!/usr/bin/env python3
"""
ワードクラウドWebアプリケーションのE2Eテスト
軽量で確実な方法でアプリケーションの動作を検証
"""

import requests
import json
import base64
import time
from pathlib import Path
import sys

class WordCloudE2ETest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def test_server_status(self):
        """サーバー稼働確認"""
        print("🧪 Test 1: サーバー稼働確認")
        try:
            response = self.session.get(self.base_url)
            assert response.status_code == 200, f"ステータスコード: {response.status_code}"
            assert "日本語ワードクラウド設定ツール" in response.text
            print("✅ サーバーは正常に稼働しています")
            return True
        except Exception as e:
            print(f"❌ サーバーエラー: {e}")
            return False
    
    def test_api_fonts(self):
        """フォントAPI確認"""
        print("\n🧪 Test 2: フォントAPI確認")
        try:
            response = self.session.get(f"{self.base_url}/api/fonts")
            assert response.status_code == 200
            data = response.json()
            
            assert "fonts" in data
            assert "count" in data
            assert data["count"] == 4
            
            # フォント確認
            font_names = ["IPAexGothic", "IPAexMincho", "IPAGothic", "IPAMincho"]
            for font_name in font_names:
                assert font_name in data["fonts"], f"{font_name}が見つかりません"
                font_info = data["fonts"][font_name]
                assert "path" in font_info
                # 相対パスをプロジェクトルートからの絶対パスに変換して確認
                font_path = Path(font_info["path"])
                if not font_path.is_absolute():
                    font_path = Path(__file__).parent.parent / font_path
                assert font_path.exists(), f"フォントファイルが存在しません: {font_path}"
            
            print(f"✅ {data['count']}個のフォントが利用可能")
            for name, info in data["fonts"].items():
                print(f"   - {info['name']}: {info['path']}")
            return True
            
        except Exception as e:
            print(f"❌ フォントAPIエラー: {e}")
            return False
    
    def test_api_sample_texts(self):
        """サンプルテキストAPI確認"""
        print("\n🧪 Test 3: サンプルテキストAPI確認")
        try:
            response = self.session.get(f"{self.base_url}/api/sample-texts")
            assert response.status_code == 200
            data = response.json()
            
            assert "texts" in data
            expected_texts = ["science_education", "japanese_general", "technology", "custom"]
            
            for text_key in expected_texts:
                assert text_key in data["texts"], f"{text_key}が見つかりません"
            
            print("✅ サンプルテキストが正常に取得できました")
            for key, info in data["texts"].items():
                if key != "custom":
                    print(f"   - {info['name']}: {len(info['text'])}文字")
            return True
            
        except Exception as e:
            print(f"❌ サンプルテキストAPIエラー: {e}")
            return False
    
    def test_api_colormaps(self):
        """カラーマップAPI確認"""
        print("\n🧪 Test 4: カラーマップAPI確認")
        try:
            response = self.session.get(f"{self.base_url}/api/colormaps")
            assert response.status_code == 200
            data = response.json()
            
            assert "colormaps" in data
            assert len(data["colormaps"]) > 10
            assert "viridis" in data["colormaps"]
            
            print(f"✅ {len(data['colormaps'])}個のカラーマップが利用可能")
            return True
            
        except Exception as e:
            print(f"❌ カラーマップAPIエラー: {e}")
            return False
    
    def test_wordcloud_generation(self):
        """ワードクラウド生成テスト"""
        print("\n🧪 Test 5: ワードクラウド生成テスト")
        
        # テスト設定
        configs = [
            {
                "name": "デフォルト設定",
                "config": {
                    "text_source": "science_education",
                    "font": "IPAexGothic",
                    "width": 800,
                    "height": 400,
                    "max_words": 50,
                    "background_color": "white",
                    "colormap": "viridis"
                }
            },
            {
                "name": "カスタムテキスト",
                "config": {
                    "text_source": "custom",
                    "custom_text": "東京工業大学 出前授業 ナトリウム 塩化ナトリウム 実験 観察",
                    "font": "IPAMincho",
                    "width": 600,
                    "height": 300,
                    "max_words": 30,
                    "background_color": "black",
                    "colormap": "rainbow"
                }
            }
        ]
        
        all_success = True
        for test_case in configs:
            print(f"\n   📋 {test_case['name']}のテスト...")
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{self.base_url}/api/generate",
                    json=test_case["config"],
                    headers={"Content-Type": "application/json"}
                )
                elapsed_time = time.time() - start_time
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] == True
                assert "image" in data
                assert len(data["image"]) > 1000  # 画像データが存在
                
                # Base64デコード確認
                image_data = base64.b64decode(data["image"])
                assert len(image_data) > 1000
                
                print(f"   ✅ 生成成功 (時間: {elapsed_time:.2f}秒)")
                
            except Exception as e:
                print(f"   ❌ 生成エラー: {e}")
                all_success = False
        
        return all_success
    
    def test_export_config(self):
        """設定エクスポートテスト"""
        print("\n🧪 Test 6: 設定エクスポートテスト")
        try:
            test_config = {
                "text_source": "science_education",
                "font": "IPAexGothic",
                "width": 800,
                "height": 400
            }
            
            response = self.session.post(
                f"{self.base_url}/api/export-config",
                json=test_config,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] == True
            assert "filename" in data
            assert "path" in data
            
            print(f"✅ 設定エクスポート成功: {data['filename']}")
            return True
            
        except Exception as e:
            print(f"❌ エクスポートエラー: {e}")
            return False
    
    def test_static_resources(self):
        """静的リソース確認"""
        print("\n🧪 Test 7: 静的リソース確認")
        resources = [
            "/static/css/style.css",
            "/static/js/app.js"
        ]
        
        all_success = True
        for resource in resources:
            try:
                response = self.session.get(f"{self.base_url}{resource}")
                assert response.status_code == 200
                assert len(response.text) > 100
                print(f"   ✅ {resource}: OK ({len(response.text)}バイト)")
            except Exception as e:
                print(f"   ❌ {resource}: エラー - {e}")
                all_success = False
        
        return all_success
    
    def run_all_tests(self):
        """全テスト実行"""
        print("🚀 ワードクラウドアプリE2Eテスト開始")
        print("=" * 50)
        
        tests = [
            self.test_server_status,
            self.test_api_fonts,
            self.test_api_sample_texts,
            self.test_api_colormaps,
            self.test_wordcloud_generation,
            self.test_export_config,
            self.test_static_resources
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"⚠️  テスト実行エラー: {e}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 テスト結果サマリー")
        print(f"   ✅ 成功: {passed}")
        print(f"   ❌ 失敗: {failed}")
        print(f"   📈 成功率: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 すべてのテストが成功しました！")
        else:
            print("\n⚠️  一部のテストが失敗しました。")
        
        return failed == 0


def main():
    """メイン実行"""
    tester = WordCloudE2ETest()
    
    # サーバー起動確認（最大10秒待機）
    print("🔍 サーバー起動確認中...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:5000", timeout=1)
            if response.status_code == 200:
                print("✅ サーバーが起動しています")
                break
        except:
            if i < 9:
                print(f"   待機中... ({i+1}/10)")
                time.sleep(1)
            else:
                print("❌ サーバーに接続できません")
                sys.exit(1)
    
    # テスト実行
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()