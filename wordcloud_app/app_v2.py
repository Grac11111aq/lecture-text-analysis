#!/usr/bin/env python3
"""
日本語ワードクラウド設定ツール Ver.2 - 単語除外テスト用
固定ビジュアルパラメータとアクセシビリティ改善版
ポート5002で動作

実行方法: python wordcloud_app/app_v2.py
アクセス: http://localhost:5002
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
from matplotlib.colors import ListedColormap

# プロジェクトルートをパスに追加
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

app = Flask(__name__)
CORS(app)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordCloudGeneratorV2:
    """ワードクラウド生成クラス Ver.2 - 固定パラメータ版"""
    
    # 固定ビジュアルパラメータ
    FIXED_PARAMS = {
        'min_font_size': 24,
        'max_font_size': 174,
        'prefer_horizontal': 0.9,
        'relative_scaling': 0.4,
        'max_words': 140,
        'background_color': '#f8f8f8'
    }
    
    # アクセシブルカラー（WCAG 2.1 Level AA準拠）
    ACCESSIBLE_COLORS = {
        'orange': '#d06500',  # より濃いオレンジ
        'blue': '#0066cc',    # より濃いブルー
        'brown': '#331a00'    # ダークブラウン
    }
    
    def __init__(self):
        self.fonts_dir = project_root / "fonts"
        self.load_available_fonts()
        self.load_sample_texts()
        self.tokenizer = Tokenizer()
        self.create_accessible_colormaps()
        
        # 除外可能な日本語ストップワード（ユーザーが選択可能）
        self.default_stop_words = set([
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
        
        # カテゴリー別の除外単語（ユーザーが選択可能）
        self.category_stop_words = {
            'general': ['みなさん', '今日', 'よう', 'こと', 'もの', 'ます', 'でし', 'まし'],
            'thanks': ['ありがとう', 'ござい', 'ました', 'てくれ', 'くださり', 'ください'],
            'school': ['東京高専', '授業', '先生', '勉強', '学習'],
            'experiment': ['実験', '観察', 'やり', 'でき']
        }
    
    def create_accessible_colormaps(self):
        """アクセシブルなカラーマップを作成"""
        # メインアクセシブル3色カラーマップ
        accessible_colors = [
            self.ACCESSIBLE_COLORS['orange'],
            self.ACCESSIBLE_COLORS['blue'],
            self.ACCESSIBLE_COLORS['brown']
        ]
        self.accessible_colormap = ListedColormap(accessible_colors, name='accessible_three')
        
        # バリエーション1: オレンジ中心
        orange_focused = [
            self.ACCESSIBLE_COLORS['orange'],
            self.ACCESSIBLE_COLORS['orange'],
            self.ACCESSIBLE_COLORS['blue'],
            self.ACCESSIBLE_COLORS['brown']
        ]
        self.orange_focused = ListedColormap(orange_focused, name='orange_focused')
        
        # バリエーション2: ブルー中心
        blue_focused = [
            self.ACCESSIBLE_COLORS['blue'],
            self.ACCESSIBLE_COLORS['blue'],
            self.ACCESSIBLE_COLORS['orange'],
            self.ACCESSIBLE_COLORS['brown']
        ]
        self.blue_focused = ListedColormap(blue_focused, name='blue_focused')
        
        # バリエーション3: バランス
        balanced_colors = [
            self.ACCESSIBLE_COLORS['brown'],
            self.ACCESSIBLE_COLORS['orange'],
            self.ACCESSIBLE_COLORS['blue'],
            self.ACCESSIBLE_COLORS['brown']
        ]
        self.balanced_colormap = ListedColormap(balanced_colors, name='balanced')
        
        # カラーマップ辞書
        self.custom_colormaps = {
            'accessible_three': self.accessible_colormap,
            'orange_focused': self.orange_focused,
            'blue_focused': self.blue_focused,
            'balanced': self.balanced_colormap
        }
        
    def load_available_fonts(self):
        """利用可能フォント読み込み"""
        font_list_path = self.fonts_dir / "font_list.json"
        
        if font_list_path.exists():
            with open(font_list_path, 'r', encoding='utf-8') as f:
                self.available_fonts = json.load(f)
        else:
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
    
    def tokenize_japanese(self, text, excluded_words=None):
        """日本語テキストを単語に分割（除外単語を考慮）"""
        # 除外単語セットを作成
        stop_words = self.default_stop_words.copy()
        if excluded_words:
            stop_words.update(excluded_words)
        
        # 単語を抽出（名詞、動詞、形容詞、副詞のみ）
        words = []
        for token in self.tokenizer.tokenize(text):
            part_of_speech = token.part_of_speech.split(',')[0]
            if part_of_speech in ['名詞', '動詞', '形容詞', '副詞']:
                # 基本形を取得
                base_form = token.base_form
                word = base_form if base_form != '*' else token.surface
                
                # 2文字以上かつストップワードでない単語のみを追加
                if len(word) >= 2 and word not in stop_words:
                    words.append(word)
        return ' '.join(words)
    
    def generate_wordcloud(self, config):
        """ワードクラウド生成（固定パラメータ使用）"""
        try:
            # テキスト取得
            text_key = config.get('text_source', 'all_responses')
            if text_key == 'custom':
                text = config.get('custom_text', '')
            else:
                text = self.sample_texts.get(text_key, {}).get('text', '')
            
            if not text.strip():
                return None, "テキストが空です"
            
            # 除外単語の収集
            excluded_words = set()
            if config.get('exclude_categories'):
                for category in config.get('exclude_categories', []):
                    if category in self.category_stop_words:
                        excluded_words.update(self.category_stop_words[category])
            
            # カスタム除外単語を追加
            if config.get('custom_exclude_words'):
                custom_words = [w.strip() for w in config.get('custom_exclude_words', '').split(',') if w.strip()]
                excluded_words.update(custom_words)
            
            # 日本語テキストを単語に分割（除外単語を適用）
            tokenized_text = self.tokenize_japanese(text, excluded_words)
            
            # フォント設定
            font_key = config.get('font', 'default')
            font_info = self.available_fonts.get(font_key, {})
            font_path = font_info.get('path')
            
            # 相対パスを絶対パスに変換
            if font_path and not Path(font_path).is_absolute():
                font_path = str(project_root / font_path)
            
            # カラーマップを選択（アクセシブルカラーマップのみ）
            colormap_name = config.get('colormap', 'accessible_three')
            colormap = self.custom_colormaps.get(colormap_name, self.accessible_colormap)
            
            # 固定パラメータを使用したワードクラウド設定
            wordcloud_config = {
                'width': config.get('width', 1000),
                'height': config.get('height', 600),
                'background_color': self.FIXED_PARAMS['background_color'],
                'max_words': self.FIXED_PARAMS['max_words'],
                'colormap': colormap,
                'relative_scaling': self.FIXED_PARAMS['relative_scaling'],
                'min_font_size': self.FIXED_PARAMS['min_font_size'],
                'max_font_size': self.FIXED_PARAMS['max_font_size'],
                'prefer_horizontal': self.FIXED_PARAMS['prefer_horizontal'],
                'collocations': False,
                'regexp': r'[\w]+',
                'include_numbers': False,
                'normalize_plurals': False,
                'stopwords': set()  # 既に除外処理済みなので空セット
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
generator = WordCloudGeneratorV2()

@app.route('/')
def index():
    """メインページ（Ver.2用テンプレート）"""
    return render_template('index_v2.html')

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
            'config': config,
            'fixed_params': generator.FIXED_PARAMS
        })
        
    except Exception as e:
        logger.error(f"API エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/fixed-params')
def get_fixed_params():
    """固定パラメータ取得"""
    return jsonify({
        'fixed_params': generator.FIXED_PARAMS,
        'accessible_colors': generator.ACCESSIBLE_COLORS
    })

@app.route('/api/stop-words')
def get_stop_words():
    """除外可能な単語カテゴリー取得"""
    return jsonify({
        'categories': {
            'general': {
                'name': '一般的な単語',
                'words': list(generator.category_stop_words['general'])
            },
            'thanks': {
                'name': '感謝の表現',
                'words': list(generator.category_stop_words['thanks'])
            },
            'school': {
                'name': '学校関連',
                'words': list(generator.category_stop_words['school'])
            },
            'experiment': {
                'name': '実験関連',
                'words': list(generator.category_stop_words['experiment'])
            }
        }
    })

@app.route('/api/colormaps')
def get_colormaps():
    """利用可能カラーマップ取得（アクセシブル版のみ）"""
    accessible_maps = [
        'accessible_three',
        'orange_focused',
        'blue_focused',
        'balanced'
    ]
    
    return jsonify({'colormaps': accessible_maps})

@app.route('/api/export-config', methods=['POST'])
def export_config():
    """設定エクスポート"""
    try:
        config = request.json
        
        # 固定パラメータも含めてエクスポート
        full_config = config.copy()
        full_config['fixed_params'] = generator.FIXED_PARAMS
        full_config['version'] = 'v2_accessible'
        
        # 設定をJSONファイルとして保存
        exports_dir = project_root / "outputs" / "wordcloud_configs"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wordcloud_config_v2_{timestamp}.json"
        config_path = exports_dir / filename
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(full_config, f, ensure_ascii=False, indent=2)
        
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

if __name__ == '__main__':
    # ログディレクトリ確保
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    print("🌨 東京高専 出前授業分析 - ワードクラウドツール Ver.2")
    print("=" * 60)
    print("🎯 単語除外テスト版（固定ビジュアルパラメータ）")
    print(f"🌐 アクセスURL: http://localhost:5002")
    print(f"📁 フォントディレクトリ: {generator.fonts_dir}")
    print(f"📊 利用可能フォント数: {len(generator.available_fonts)}")
    print("♿ アクセシブルカラー: オレンジ(#d06500)・ブルー(#0066cc)・ブラウン(#331a00)")
    print("🔧 固定パラメータ:")
    for key, value in generator.FIXED_PARAMS.items():
        print(f"   - {key}: {value}")
    print("=" * 60)
    
    # Flaskアプリ実行（ポート5002）
    app.run(debug=True, host='0.0.0.0', port=5002)