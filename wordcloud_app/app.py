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
import pandas as pd
from janome.tokenizer import Tokenizer
from matplotlib.colors import LinearSegmentedColormap

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
        self.tokenizer = Tokenizer()
        self.create_custom_colormaps()
        
        # 日本語ストップワード
        self.stop_words = set([
            'て', 'に', 'を', 'は', 'が', 'で', 'と', 'し', 'れ', 'さ', 'ある', 'いる', 
            'も', 'する', 'から', 'な', 'こと', 'です', 'だ', 'た', 'した', 'の', 'よう',
            'れる', 'くる', 'や', 'くれ', 'そう', 'ない', 'か', 'ので', 'よ', 'てる',
            'もの', 'み', 'また', 'その', 'あり', 'き', 'い', 'う', 'のは', 'ん',
            'のが', 'もん', 'どう', 'など', 'マス', '。', '、', '（', '）', '(', ')',
            'より', 'へ', 'まで', 'から', 'また', 'も', 'お', 'みなさん', '今日',
            'ありがとう', 'ござい', 'ました', 'てくれ', 'くれる', 'てくれる',
            'くださり', 'ください', 'ませ', 'ありがとうござい',
            '東京高専', 'みなさん', '本当', '一番', '授業', 'でき', 'いっ',
            'おもしろ', 'すご', 'よかっ', 'より', 'こと', '今日', 'そう', 'な',
            'て', 'る', 'よう', 'に', 'で', 'と', 'から', '。', '、', 'が',
            'ミンチ', 'カルシウム', 'バリウム', 'リチウム', 'ホウ酸',
            'ユキ', 'スケッチ', 'いう', 'べき', 'だっ', 'つい', 'った',
            'とっ', 'おもしろい', 'きれい', 'すごい', 'なる', 'みる', 'いく',
            'れ', 'なり', 'やっ', 'たい', 'いい', 'それ', 'お'
        ])
    
    def create_custom_colormaps(self):
        """カスタムカラーマップを作成"""
        n_bins = 100
        
        # 3色限定カラーマップ（ダークグレー、濃いオレンジ、濃い青）
        three_colors = ['#404040', '#CC4400', '#003366']  # ダークグレー、濃いオレンジ、濃い青
        self.three_color_scheme = LinearSegmentedColormap.from_list('three_color_scheme', three_colors, N=n_bins)
        
        # 3色のシンプルバージョン（より濃い色）
        three_colors_dark = ['#333333', '#B8860B', '#002244']  # より濃いグレー、ダークゴールド、ネイビー
        self.three_color_dark = LinearSegmentedColormap.from_list('three_color_dark', three_colors_dark, N=n_bins)
        
        # 3色のバランス版（グレーを中心に）
        three_colors_balanced = ['#555555', '#CC4400', '#003366', '#555555']  # グレー中心
        self.three_color_balanced = LinearSegmentedColormap.from_list('three_color_balanced', three_colors_balanced, N=n_bins)
        
        # 指定された3色のみを使用するカラーマップ（#ee7800, #0077ed, #331a00）
        from matplotlib.colors import ListedColormap
        specified_colors_only = ['#ee7800', '#0077ed', '#331a00']  # オレンジ、ブルー、ダークブラウン
        self.specified_three_colors = ListedColormap(specified_colors_only, name='specified_three_colors')
        
        # 指定3色のみの順序バリエーション
        specified_balanced_only = ['#331a00', '#ee7800', '#0077ed']  # ダークブラウン、オレンジ、ブルー
        self.specified_balanced = ListedColormap(specified_balanced_only, name='specified_balanced')
        
        # 指定3色のみの明るい順序
        specified_bright_only = ['#0077ed', '#ee7800', '#331a00']  # ブルー、オレンジ、ダークブラウン
        self.specified_bright = ListedColormap(specified_bright_only, name='specified_bright')
        
        # 指定3色を使った拡張版（色の重複で分布を調整）
        specified_weighted = ['#ee7800', '#ee7800', '#0077ed', '#0077ed', '#331a00', '#331a00']  # 各色を2回ずつ
        self.specified_weighted = ListedColormap(specified_weighted, name='specified_weighted')
        
        # オレンジから青へのグラデーション（従来）
        colors1 = ['#FF6B00', '#FF8C00', '#FFA500', '#FFB84D', '#FFD700', 
                  '#87CEEB', '#4682B4', '#1E90FF', '#0066CC', '#003D7A']
        self.orange_blue = LinearSegmentedColormap.from_list('orange_blue', colors1, N=n_bins)
        
        # 青からオレンジへのグラデーション（従来）
        colors2 = ['#003D7A', '#0066CC', '#1E90FF', '#4682B4', '#87CEEB',
                  '#FFD700', '#FFB84D', '#FFA500', '#FF8C00', '#FF6B00']
        self.blue_orange = LinearSegmentedColormap.from_list('blue_orange', colors2, N=n_bins)
        
        # オレンジ・青のバランスカラー（従来）
        colors3 = ['#FF6B00', '#FF8C00', '#FFA500', '#FFD700', '#FFFF00',
                  '#FFFFFF', '#87CEEB', '#4682B4', '#1E90FF', '#003D7A']
        self.orange_white_blue = LinearSegmentedColormap.from_list('orange_white_blue', colors3, N=n_bins)
        
        # 東京高専カラー（暖色系）
        colors4 = ['#FF4500', '#FF6347', '#FF7F50', '#FFA07A', '#FFB347',
                  '#FFD700', '#FFA500', '#FF8C00', '#FF6B00', '#FF4500']
        self.tokyo_kosen_warm = LinearSegmentedColormap.from_list('tokyo_kosen_warm', colors4, N=n_bins)
        
        # 東京高専カラー（寒色系）
        colors5 = ['#000080', '#0000CD', '#0000FF', '#1E90FF', '#4169E1',
                  '#4682B4', '#5F9EA0', '#6495ED', '#87CEEB', '#ADD8E6']
        self.tokyo_kosen_cool = LinearSegmentedColormap.from_list('tokyo_kosen_cool', colors5, N=n_bins)
        
        # カスタムカラーマップを辞書で保持
        self.custom_colormaps = {
            'specified_three_colors': self.specified_three_colors,
            'specified_balanced': self.specified_balanced,
            'specified_bright': self.specified_bright,
            'specified_weighted': self.specified_weighted,
            'three_color_scheme': self.three_color_scheme,
            'three_color_dark': self.three_color_dark,
            'three_color_balanced': self.three_color_balanced,
            'orange_blue': self.orange_blue,
            'blue_orange': self.blue_orange,
            'orange_white_blue': self.orange_white_blue,
            'tokyo_kosen_warm': self.tokyo_kosen_warm,
            'tokyo_kosen_cool': self.tokyo_kosen_cool
        }
        
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
        """実際のプロジェクトデータを読み込み"""
        try:
            # 実際のデータを読み込む
            data_path = project_root / "data" / "processed" / "all_text_corpus.csv"
            if data_path.exists():
                df = pd.read_csv(data_path)
                
                # カテゴリー別にテキストを結合
                comments_text = ' '.join(df[df['category'] == '感想文']['text'].tolist())
                before_text = ' '.join(df[df['category'] == 'Q2理由_授業前']['text'].tolist())
                after_text = ' '.join(df[df['category'] == 'Q2理由_授業後']['text'].tolist())
                all_text = ' '.join(df['text'].tolist())
                
                self.sample_texts = {
                    "all_responses": {
                        "name": "全回答（統合）",
                        "text": all_text
                    },
                    "comments": {
                        "name": "感想文のみ",
                        "text": comments_text
                    },
                    "q2_before": {
                        "name": "授業前（なぜしょっぱい？）",
                        "text": before_text
                    },
                    "q2_after": {
                        "name": "授業後（なぜしょっぱい？）",
                        "text": after_text
                    },
                    "custom": {
                        "name": "カスタムテキスト",
                        "text": ""
                    }
                }
                logger.info("実際のプロジェクトデータを読み込みました")
            else:
                # フォールバック：デフォルトテキスト
                self._load_default_texts()
        except Exception as e:
            logger.error(f"データ読み込みエラー: {e}")
            self._load_default_texts()
    
    def _load_default_texts(self):
        """デフォルトのサンプルテキスト"""
        self.sample_texts = {
            "science_education": {
                "name": "科学教育（サンプル）",
                "text": """東京工業大学 出前授業 ナトリウム 塩化ナトリウム 炎色反応 実験 観察 科学 学習 
                         面白い すごい きれい 発見 理解 知識 研究 体験 感動 びっくり"""
            },
            "custom": {
                "name": "カスタムテキスト",
                "text": ""
            }
        }
    
    def tokenize_japanese(self, text):
        """日本語テキストを単語に分割"""
        # 単語を抽出（名詞、動詞、形容詞、副詞のみ）
        words = []
        for token in self.tokenizer.tokenize(text):
            part_of_speech = token.part_of_speech.split(',')[0]
            if part_of_speech in ['名詞', '動詞', '形容詞', '副詞']:
                # 基本形を取得
                base_form = token.base_form
                word = base_form if base_form != '*' else token.surface
                
                # 2文字以上かつストップワードでない単語のみを追加
                if len(word) >= 2 and word not in self.stop_words:
                    words.append(word)
        return ' '.join(words)
    
    def generate_wordcloud(self, config):
        """ワードクラウド生成"""
        try:
            # テキスト取得
            text_key = config.get('text_source', 'all_responses')
            if text_key == 'custom':
                text = config.get('custom_text', '')
            else:
                text = self.sample_texts.get(text_key, {}).get('text', '')
            
            if not text.strip():
                return None, "テキストが空です"
            
            # 日本語テキストを単語に分割
            tokenized_text = self.tokenize_japanese(text)
            
            # フォント設定
            font_key = config.get('font', 'default')
            font_info = self.available_fonts.get(font_key, {})
            font_path = font_info.get('path')
            
            # 相対パスを絶対パスに変換
            if font_path and not Path(font_path).is_absolute():
                font_path = str(project_root / font_path)
            
            # 背景色設定（明度から生成またはデフォルト）
            background_color = config.get('background_color')
            if not background_color or background_color.strip() == '':
                # background_brightnessから背景色を生成（90-100%の明るい範囲）
                slider_value = config.get('background_brightness', 50)  # スライダー値
                # スライダー値（0-100）を実際の明度（90-100%）にマッピング
                actual_brightness = 90 + (slider_value / 100) * 10
                # 明度をグレースケールHEXに変換
                value = int((actual_brightness / 100) * 255)
                background_color = f'#{value:02x}{value:02x}{value:02x}'
                logger.info(f"背景色を明度から生成: スライダー{slider_value}% -> 実際{actual_brightness:.1f}% -> {background_color}")
            
            # 白色の場合はライトグレーに変更
            if background_color.lower() == 'white' or background_color == '#ffffff':
                background_color = '#f2f2f2'  # より明るいグレー
            
            # カラーマップを選択
            colormap_name = config.get('colormap', 'orange_blue')
            
            # カスタムカラーマップの処理（3色系統）
            if config.get('use_custom_colors', False) and config.get('custom_colors'):
                custom_colors = config.get('custom_colors', [])
                if len(custom_colors) >= 3:
                    # 3色からグラデーションカラーマップを作成
                    # オレンジ系、グレー系、ブルー系の順序でカラーマップを構築
                    expanded_colors = [
                        custom_colors[1],  # グレー系（中央）
                        custom_colors[0],  # オレンジ系  
                        custom_colors[2],  # ブルー系
                        custom_colors[1]   # グレー系（終端）
                    ]
                    
                    n_bins = 100
                    custom_colormap = LinearSegmentedColormap.from_list(
                        'user_custom_3color', expanded_colors, N=n_bins
                    )
                    colormap = custom_colormap
                    logger.info(f"3色カスタムカラーマップを使用: {custom_colors}")
                elif len(custom_colors) >= 2:
                    # 2色の場合
                    n_bins = 100
                    custom_colormap = LinearSegmentedColormap.from_list(
                        'user_custom_2color', custom_colors, N=n_bins
                    )
                    colormap = custom_colormap
                    logger.info(f"2色カスタムカラーマップを使用: {custom_colors}")
                else:
                    colormap = self.custom_colormaps.get(colormap_name, colormap_name)
            else:
                colormap = self.custom_colormaps.get(colormap_name, colormap_name)
            
            wordcloud_config = {
                'width': config.get('width', 800),
                'height': config.get('height', 400),
                'background_color': background_color,
                'max_words': config.get('max_words', 100),
                'colormap': colormap,
                'relative_scaling': config.get('relative_scaling', 0.5),
                'min_font_size': config.get('min_font_size', 10),
                'max_font_size': config.get('max_font_size', 100),
                'prefer_horizontal': config.get('prefer_horizontal', 0.7),
                'collocations': False,
                'regexp': r'[\w]+',
                'include_numbers': False,
                'normalize_plurals': False,
                'stopwords': self.stop_words
            }
            
            if font_path:
                wordcloud_config['font_path'] = font_path
            
            # ワードクラウド生成
            wordcloud = WordCloud(**wordcloud_config).generate(tokenized_text)
            
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
        "specified_colors_v1": {
            "name": "指定3色（#ee7800・#0077ed・#331a00）",
            "config": {
                "text_source": "all_responses",
                "width": 1000,
                "height": 600,
                "background_brightness": 60,  # スライダー値60 = 実際の96%明度
                "max_words": 60,
                "colormap": "specified_three_colors",
                "relative_scaling": 0.6,
                "min_font_size": 16,
                "max_font_size": 90,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "specified_colors_v2": {
            "name": "指定3色・バランス版",
            "config": {
                "text_source": "comments",
                "width": 800,
                "height": 400,
                "background_brightness": 70,  # スライダー値70 = 実際の97%明度
                "max_words": 50,
                "colormap": "specified_balanced",
                "relative_scaling": 0.5,
                "min_font_size": 14,
                "max_font_size": 70,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "specified_colors_v3": {
            "name": "指定3色・明るい版",
            "config": {
                "text_source": "q2_after",
                "width": 900,
                "height": 500,
                "background_brightness": 80,  # スライダー値80 = 実際の98%明度
                "max_words": 40,
                "colormap": "specified_bright",
                "relative_scaling": 0.5,
                "min_font_size": 16,
                "max_font_size": 80,
                "prefer_horizontal": 0.7,
                "collocations": False
            }
        },
        "specified_colors_presentation": {
            "name": "指定3色・発表用",
            "config": {
                "text_source": "all_responses",
                "width": 1200,
                "height": 800,
                "background_brightness": 75,  # スライダー値75 = 実際の97.5%明度
                "max_words": 50,
                "colormap": "specified_three_colors",
                "relative_scaling": 0.3,
                "min_font_size": 20,
                "max_font_size": 120,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "specified_colors_weighted": {
            "name": "指定3色・重み付き分布",
            "config": {
                "text_source": "comments",
                "width": 800,
                "height": 400,
                "background_brightness": 65,  # スライダー値65 = 実際の96.5%明度
                "max_words": 50,
                "colormap": "specified_weighted",
                "relative_scaling": 0.5,
                "min_font_size": 14,
                "max_font_size": 70,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "custom_orange_gray_blue": {
            "name": "カスタム3色（オレンジ・グレー・ブルー）",
            "config": {
                "text_source": "all_responses",
                "width": 1000,
                "height": 600,
                "background_brightness": 20,  # スライダー値20 = 実際の92%明度
                "max_words": 60,
                "use_custom_colors": True,
                "colormap": "custom",
                "relative_scaling": 0.6,
                "min_font_size": 16,
                "max_font_size": 90,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "custom_bright_contrast": {
            "name": "カスタム3色・感想文（高コントラスト）",
            "config": {
                "text_source": "comments",
                "width": 800,
                "height": 400,
                "background_brightness": 50,  # スライダー値50 = 実際の95%明度
                "max_words": 50,
                "use_custom_colors": True,
                "colormap": "custom",
                "relative_scaling": 0.5,
                "min_font_size": 14,
                "max_font_size": 70,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "custom_presentation": {
            "name": "カスタム3色・発表用（プレゼン向け）",
            "config": {
                "text_source": "q2_after",
                "width": 1200,
                "height": 800,
                "background_brightness": 0,  # スライダー値0 = 実際の90%明度
                "max_words": 40,
                "use_custom_colors": True,
                "colormap": "custom",
                "relative_scaling": 0.3,
                "min_font_size": 20,
                "max_font_size": 120,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "minimal_gray": {
            "name": "ミニマル（薄グレー背景）",
            "config": {
                "width": 600,
                "height": 300,
                "background_brightness": 80,  # スライダー値80 = 実際の98%明度
                "max_words": 30,
                "colormap": "three_color_scheme",
                "relative_scaling": 0.2,
                "min_font_size": 15,
                "max_font_size": 60,
                "prefer_horizontal": 0.9,
                "collocations": False
            }
        },
        "production": {
            "name": "本番用（東京高専）",
            "config": {
                "text_source": "all_responses",
                "width": 1000,
                "height": 600,
                "background_brightness": 50,  # スライダー値50 = 実際の95%明度
                "max_words": 60,
                "colormap": "orange_blue",
                "relative_scaling": 0.6,
                "min_font_size": 16,
                "max_font_size": 90,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "comments_only": {
            "name": "感想文のみ",
            "config": {
                "text_source": "comments",
                "width": 800,
                "height": 400,
                "background_brightness": 50,  # スライダー値50 = 実際の95%明度
                "max_words": 50,
                "colormap": "tokyo_kosen_warm",
                "relative_scaling": 0.5,
                "min_font_size": 14,
                "max_font_size": 70,
                "prefer_horizontal": 0.8,
                "collocations": False
            }
        },
        "before_after": {
            "name": "授業前後比較",
            "config": {
                "text_source": "q2_after",
                "width": 900,
                "height": 500,
                "background_brightness": 50,  # スライダー値50 = 実際の95%明度
                "max_words": 40,
                "colormap": "blue_orange",
                "relative_scaling": 0.5,
                "min_font_size": 16,
                "max_font_size": 80,
                "prefer_horizontal": 0.7,
                "collocations": False
            }
        },
        "academic": {
            "name": "学術発表用",
            "config": {
                "width": 1200,
                "height": 800,
                "background_brightness": 50,  # スライダー値50 = 実際の95%明度
                "max_words": 50,
                "colormap": "tokyo_kosen_cool",
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
                "background_brightness": 0,  # スライダー値0 = 実際の90%明度（少し暗め）
                "max_words": 150,
                "colormap": "orange_white_blue",
                "relative_scaling": 0.7,
                "min_font_size": 8,
                "max_font_size": 80,
                "prefer_horizontal": 0.5,
                "collocations": False
            }
        }
    }
    
    return jsonify({'presets': presets})

@app.route('/api/colormaps')
def get_colormaps():
    """利用可能カラーマップ取得"""
    import matplotlib.cm as cm
    
    # 推奨カラーマップ（指定3色カラーマップを先頭に）
    recommended_maps = [
        'specified_three_colors', 'specified_balanced', 'specified_bright', 'specified_weighted',
        'three_color_scheme', 'three_color_dark', 'three_color_balanced',
        'orange_blue', 'blue_orange', 'orange_white_blue', 
        'tokyo_kosen_warm', 'tokyo_kosen_cool',
        'Oranges', 'Blues', 'RdBu', 'BuOr', 'PuOr', 'coolwarm',
        'Set2', 'Set3', 'Pastel1', 'Pastel2',
        'viridis', 'plasma', 'inferno', 'magma',
        'copper', 'autumn', 'winter', 'spring', 'summer',
        'tab10', 'tab20', 'gray'
    ]
    
    return jsonify({'colormaps': recommended_maps})

if __name__ == '__main__':
    # ログディレクトリ確保
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    print("🌨 東京高専 出前授業分析 - ワードクラウドツール")
    print("=" * 60)
    print(f"🌐 アクセスURL: http://localhost:5001")
    print(f"📁 フォントディレクトリ: {generator.fonts_dir}")
    print(f"📊 利用可能フォント数: {len(generator.available_fonts)}")
    print("🔥 カスタムカラーマップ: オレンジ+青系")
    print("🤖 日本語形態素解析: Janome使用")
    print("=" * 60)
    
    # Flaskアプリ実行
    app.run(debug=True, host='0.0.0.0', port=5001)