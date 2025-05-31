#!/usr/bin/env python3
"""
日本語フォント自動ダウンロード・セットアップスクリプト
ワードクラウド用の各種日本語フォントを取得・配置

実行方法: python scripts/setup/download_japanese_fonts.py
"""

import os
import sys
import requests
import zipfile
import logging
from pathlib import Path
from urllib.parse import urlparse
import shutil
import subprocess

class JapaneseFontDownloader:
    """日本語フォントダウンローダー"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.fonts_dir = Path("fonts")
        self.fonts_dir.mkdir(exist_ok=True)
        
        # 日本語フォント一覧
        self.font_sources = {
            "IPAexGothic": {
                "name": "IPAex Gothic", 
                "url": "https://moji.or.jp/wp-content/ipafont/IPAexfont/IPAexfont00401.zip",
                "filename": "ipaexg.ttf",
                "description": "IPA フォント（ゴシック）"
            },
            "IPAexMincho": {
                "name": "IPAex Mincho",
                "url": "https://moji.or.jp/wp-content/ipafont/IPAexfont/IPAexfont00401.zip", 
                "filename": "ipaexm.ttf",
                "description": "IPA フォント（明朝）"
            },
            "IPAGothic": {
                "name": "IPA Gothic",
                "url": "https://moji.or.jp/wp-content/ipafont/IPAfont/IPAfont00303.zip",
                "filename": "ipag.ttf",
                "description": "IPA ゴシック"
            },
            "IPAMincho": {
                "name": "IPA Mincho", 
                "url": "https://moji.or.jp/wp-content/ipafont/IPAfont/IPAfont00303.zip",
                "filename": "ipam.ttf",
                "description": "IPA 明朝"
            }
        }
    
    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/font_download.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def download_file(self, url, destination):
        """ファイルダウンロード"""
        try:
            self.logger.info(f"ダウンロード開始: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(destination, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r進捗: {progress:.1f}%", end='', flush=True)
            
            print()  # 改行
            self.logger.info(f"ダウンロード完了: {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"ダウンロードエラー {url}: {e}")
            return False
    
    def extract_zip(self, zip_path, extract_to):
        """ZIPファイル展開"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            self.logger.info(f"展開完了: {zip_path} -> {extract_to}")
            return True
        except Exception as e:
            self.logger.error(f"展開エラー {zip_path}: {e}")
            return False
    
    def find_font_file(self, directory, target_filename):
        """指定されたフォントファイルを検索"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower() == target_filename.lower():
                    return Path(root) / file
        return None
    
    def download_font(self, font_key):
        """個別フォントのダウンロード"""
        font_info = self.font_sources[font_key]
        font_name = font_info["name"]
        url = font_info["url"]
        target_filename = font_info["filename"]
        
        self.logger.info(f"フォント取得開始: {font_name}")
        
        # 既存チェック
        final_path = self.fonts_dir / target_filename
        if final_path.exists():
            self.logger.info(f"フォント既存: {font_name}")
            return str(final_path)
        
        # 一時ディレクトリ
        temp_dir = Path("temp_fonts")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # ダウンロード
            parsed_url = urlparse(url)
            temp_file = temp_dir / Path(parsed_url.path).name
            
            if not self.download_file(url, temp_file):
                return None
            
            # ZIP展開
            if temp_file.suffix.lower() == '.zip':
                extract_dir = temp_dir / f"extract_{font_key}"
                extract_dir.mkdir(exist_ok=True)
                
                if not self.extract_zip(temp_file, extract_dir):
                    return None
                
                # フォントファイル検索
                font_file = self.find_font_file(extract_dir, target_filename)
                if font_file:
                    # 最終位置にコピー
                    shutil.copy2(font_file, final_path)
                    self.logger.info(f"フォントインストール完了: {font_name}")
                else:
                    self.logger.error(f"フォントファイル未発見: {target_filename}")
                    return None
            else:
                # 直接コピー
                shutil.copy2(temp_file, final_path)
                self.logger.info(f"フォントインストール完了: {font_name}")
            
            return str(final_path)
            
        except Exception as e:
            self.logger.error(f"フォントインストールエラー {font_name}: {e}")
            return None
        finally:
            # 一時ディレクトリクリーンアップ
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def download_all_fonts(self):
        """全フォントダウンロード"""
        self.logger.info("日本語フォント一括ダウンロード開始")
        
        successful_fonts = {}
        failed_fonts = []
        
        for font_key, font_info in self.font_sources.items():
            print(f"\n📥 {font_info['description']} をダウンロード中...")
            
            font_path = self.download_font(font_key)
            if font_path:
                successful_fonts[font_key] = {
                    "name": font_info["name"],
                    "path": font_path,
                    "description": font_info["description"]
                }
                print(f"✅ {font_info['name']} インストール完了")
            else:
                failed_fonts.append(font_key)
                print(f"❌ {font_info['name']} インストール失敗")
        
        # 結果サマリー
        print(f"\n🎯 ダウンロード結果:")
        print(f"成功: {len(successful_fonts)}個")
        print(f"失敗: {len(failed_fonts)}個")
        
        if successful_fonts:
            print(f"\n✅ インストール済みフォント:")
            for key, info in successful_fonts.items():
                print(f"  - {info['name']}: {info['path']}")
        
        if failed_fonts:
            print(f"\n❌ 失敗したフォント:")
            for key in failed_fonts:
                print(f"  - {self.font_sources[key]['name']}")
        
        # フォント情報JSONファイル生成
        font_list_path = self.fonts_dir / "font_list.json"
        import json
        with open(font_list_path, 'w', encoding='utf-8') as f:
            json.dump(successful_fonts, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"フォント情報保存: {font_list_path}")
        
        return successful_fonts
    
    def test_fonts(self):
        """フォントテスト"""
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        
        test_text = "東京工業大学 出前授業 ナトリウム 塩化ナトリウム 炎色反応 実験 観察 科学 学習"
        
        font_list_path = self.fonts_dir / "font_list.json"
        if not font_list_path.exists():
            self.logger.error("フォント情報ファイルが見つかりません")
            return
        
        import json
        with open(font_list_path, 'r', encoding='utf-8') as f:
            fonts = json.load(f)
        
        print(f"\n🧪 フォントテスト開始 ({len(fonts)}個)")
        
        test_dir = Path("outputs/font_tests")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        for font_key, font_info in fonts.items():
            try:
                print(f"テスト中: {font_info['name']}")
                
                # ワードクラウド生成
                wordcloud = WordCloud(
                    font_path=font_info['path'],
                    width=400,
                    height=200,
                    background_color='white',
                    max_words=20
                ).generate(test_text)
                
                # 保存
                plt.figure(figsize=(8, 4))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.title(f'{font_info["name"]} - フォントテスト', fontsize=12)
                plt.tight_layout()
                plt.savefig(test_dir / f'{font_key}_test.png', dpi=150, bbox_inches='tight')
                plt.close()
                
                print(f"✅ {font_info['name']} テスト成功")
                
            except Exception as e:
                print(f"❌ {font_info['name']} テスト失敗: {e}")
        
        print(f"\n📁 テスト結果: {test_dir}")


def main():
    """メイン実行"""
    print("🎌 日本語フォント自動インストーラー")
    print("="*50)
    
    # ログディレクトリ確保
    Path('logs').mkdir(exist_ok=True)
    
    downloader = JapaneseFontDownloader()
    
    # フォントダウンロード
    fonts = downloader.download_all_fonts()
    
    if fonts:
        print(f"\n🎨 フォントテストを実行中...")
        downloader.test_fonts()
    
    print(f"\n🎉 セットアップ完了！")
    print(f"フォントディレクトリ: {downloader.fonts_dir}")


if __name__ == "__main__":
    main()