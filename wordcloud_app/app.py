#!/usr/bin/env python3
"""
日本語ワードクラウド設定ツール
リアルタイムでフォント・設定を調整可能なWebアプリケーション

実行方法: python wordcloud_app/app.py
アクセス: http://localhost:5000
"""

import os
import sys
import json
import base64
import io
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')  # バックエンド設定（GUI不要）
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import logging

# プロジェクトルートをパスに追加
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

app = Flask(__name__)
CORS(app)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordCloudGenerator:
    """ワードクラウド生成クラス"""
    
    def __init__(self):
        self.fonts_dir = project_root / "fonts"
        self.load_available_fonts()
        self.load_sample_texts()
        
    def load_available_fonts(self):
        """利用可能フォント読み込み"""
        font_list_path = self.fonts_dir / "font_list.json"
        
        if font_list_path.exists():
            with open(font_list_path, 'r', encoding='utf-8') as f:
                self.available_fonts = json.load(f)
        else:
            # フォールバック：デフォルトフォント
            self.available_fonts = {
                "default": {
                    "name": "Default",
                    "path": None,
                    "description": "システムデフォルト"
                }
            }
        
        logger.info(f"利用可能フォント数: {len(self.available_fonts)}")
    
    def load_sample_texts(self):
        """サンプルテキスト読み込み"""
        self.sample_texts = {
            "science_education": {
                "name": "科学教育",
                "text": """東京工業大学 出前授業 ナトリウム 塩化ナトリウム 炎色反応 実験 観察 科学 学習 
                         面白い すごい きれい 発見 理解 知識 研究 体験 感動 びっくり"""
            },
            "japanese_general": {
                "name": "日本語一般",
                "text": """日本語 ひらがな カタカナ 漢字 文字 言語 表現 美しい 文化 伝統 
                         現代 技術 発展 社会 人々 生活 自然 季節 花 桜"""
            },
            "technology": {
                "name": "技術・IT",
                "text": """コンピュータ プログラミング アルゴリズム データ 分析 可視化 
                         人工知能 機械学習 深層学習 ニューラルネットワーク 自動化 効率化"""
            },
            "custom": {
                "name": "カスタムテキスト",
                "text": ""
            }
        }
    
    def generate_wordcloud(self, config):
        """ワードクラウド生成"""
        try:
            # テキスト取得
            text_key = config.get('text_source', 'science_education')
            if text_key == 'custom':
                text = config.get('custom_text', '')
            else:
                text = self.sample_texts.get(text_key, {}).get('text', '')
            
            if not text.strip():
                return None, "テキストが空です"
            
            # フォント設定
            font_key = config.get('font', 'default')
            font_info = self.available_fonts.get(font_key, {})
            font_path = font_info.get('path')
            
            # 相対パスを絶対パスに変換
            if font_path and not Path(font_path).is_absolute():
                font_path = str(project_root / font_path)
            
            # ワードクラウド設定
            wordcloud_config = {
                'width': config.get('width', 800),
                'height': config.get('height', 400),
                'background_color': config.get('background_color', 'white'),
                'max_words': config.get('max_words', 100),
                'colormap': config.get('colormap', 'viridis'),
                'relative_scaling': config.get('relative_scaling', 0.5),
                'min_font_size': config.get('min_font_size', 10),
                'max_font_size': config.get('max_font_size', 100),
                'prefer_horizontal': config.get('prefer_horizontal', 0.7),
                'collocations': config.get('collocations', False)
            }
            
            if font_path:
                wordcloud_config['font_path'] = font_path
            
            # ワードクラウド生成
            wordcloud = WordCloud(**wordcloud_config).generate(text)
            
            # 画像変換
            plt.figure(figsize=(12, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            
            # Base64エンコード
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            return img_base64, None
            
        except Exception as e:
            logger.error(f"ワードクラウド生成エラー: {e}")
            return None, str(e)

# グローバルインスタンス
generator = WordCloudGenerator()

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/api/fonts')
def get_fonts():
    """利用可能フォント一覧取得"""
    return jsonify({
        'fonts': generator.available_fonts,
        'count': len(generator.available_fonts)
    })

@app.route('/api/sample-texts')
def get_sample_texts():
    """サンプルテキスト一覧取得"""
    return jsonify({
        'texts': generator.sample_texts
    })

@app.route('/api/generate', methods=['POST'])
def generate_wordcloud():
    """ワードクラウド生成API"""
    try:
        config = request.json
        
        img_base64, error = generator.generate_wordcloud(config)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        return jsonify({
            'success': True,
            'image': img_base64,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"API エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export-config', methods=['POST'])
def export_config():
    """設定エクスポート"""
    try:
        config = request.json
        
        # 設定をJSONファイルとして保存
        exports_dir = project_root / "outputs" / "wordcloud_configs"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wordcloud_config_{timestamp}.json"
        config_path = exports_dir / filename
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': str(config_path)
        })
        
    except Exception as e:
        logger.error(f"設定エクスポートエラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/presets')
def get_presets():
    """プリセット設定取得"""
    presets = {
        "default": {
            "name": "デフォルト",
            "config": {
                "width": 800,
                "height": 400,
                "background_color": "white",
                "max_words": 100,
                "colormap": "viridis",
                "relative_scaling": 0.5,
                "min_font_size": 10,
                "max_font_size": 100,
                "prefer_horizontal": 0.7,
                "collocations": False
            }
        },
        "academic": {
            "name": "学術発表用",
            "config": {
                "width": 1200,
                "height": 800,
                "background_color": "white",
                "max_words": 50,
                "colormap": "Blues",
                "relative_scaling": 0.3,
                "min_font_size": 20,
                "max_font_size": 120,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "colorful": {
            "name": "カラフル",
            "config": {
                "width": 800,
                "height": 600,
                "background_color": "black",
                "max_words": 150,
                "colormap": "rainbow",
                "relative_scaling": 0.7,
                "min_font_size": 8,
                "max_font_size": 80,
                "prefer_horizontal": 0.5,
                "collocations": True
            }
        },
        "minimal": {
            "name": "ミニマル",
            "config": {
                "width": 600,
                "height": 300,
                "background_color": "white",
                "max_words": 30,
                "colormap": "gray",
                "relative_scaling": 0.2,
                "min_font_size": 15,
                "max_font_size": 60,
                "prefer_horizontal": 0.9,
                "collocations": False
            }
        }
    }
    
    return jsonify({'presets': presets})

@app.route('/api/colormaps')
def get_colormaps():
    """利用可能カラーマップ取得"""
    import matplotlib.cm as cm
    
    # 推奨カラーマップ
    recommended_maps = [
        'viridis', 'plasma', 'inferno', 'magma',
        'Blues', 'Reds', 'Greens', 'Oranges', 
        'rainbow', 'coolwarm', 'seismic', 'Set1', 'Set2', 'Set3',
        'tab10', 'tab20', 'gray', 'hot', 'cool'
    ]
    
    return jsonify({'colormaps': recommended_maps})

if __name__ == '__main__':
    # ログディレクトリ確保
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    print("🎨 日本語ワードクラウド設定ツール")
    print("=" * 50)
    print(f"🌐 アクセスURL: http://localhost:5000")
    print(f"📁 フォントディレクトリ: {generator.fonts_dir}")
    print(f"📊 利用可能フォント数: {len(generator.available_fonts)}")
    print("=" * 50)
    
    # Flaskアプリ実行
    app.run(debug=True, host='0.0.0.0', port=5000)