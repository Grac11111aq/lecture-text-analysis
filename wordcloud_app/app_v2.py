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
import matplotlib.font_manager as fm
from matplotlib import font_manager as fm
from PIL import Image
import numpy as np
import logging
import pandas as pd
from janome.tokenizer import Tokenizer
from matplotlib.colors import ListedColormap
from collections import Counter
from scipy import stats
import math
import networkx as nx
from collections import defaultdict
from itertools import combinations
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import coo_matrix

# プロジェクトルートをパスに追加
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

app = Flask(__name__)
CORS(app)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DifferenceWordCloudGenerator:
    """差分ワードクラウド生成クラス"""
    
    def __init__(self, base_generator):
        """ベースジェネレータから機能を継承"""
        self.base_generator = base_generator
        self.create_difference_colormaps()
        
        # 科学用語リスト（教育効果測定用）
        self.science_terms = {
            'basic': ['塩', '食塩', '塩分'],
            'intermediate': ['ナトリウム', '塩化ナトリウム'],
            'advanced': ['Na', 'NaCl', 'イオン', 'Na+']
        }
    
    def create_difference_colormaps(self):
        """差分可視化用カラーマップ作成（アクセシブルカラー準拠）"""
        # 通常ワードクラウドのアクセシブルカラーを基準にする
        base_orange = self.base_generator.ACCESSIBLE_COLORS['orange']  # #d06500
        base_blue = self.base_generator.ACCESSIBLE_COLORS['blue']      # #0066cc
        base_brown = self.base_generator.ACCESSIBLE_COLORS['brown']    # #331a00
        
        self.difference_colors = {
            # 増加語（オレンジ系）- アクセシブルカラー準拠
            'increase_large': base_brown,    # 大幅増加（ダークブラウン）
            'increase_medium': base_orange,  # 中程度増加（アクセシブルオレンジ）
            'increase_small': '#ff9800',     # 軽微増加（明るいオレンジ）
            
            # 減少語（ブルー系）- アクセシブルカラー準拠
            'decrease_large': base_blue,     # 大幅減少（アクセシブルブルー）
            'decrease_medium': '#1976d2',    # 中程度減少（少し明るい青）
            'decrease_small': '#64b5f6',     # 軽微減少（薄い青）
            
            # 共通・科学用語
            'common': '#757575',             # 変化なし（中間グレー）
            'science_highlight': base_brown  # 科学用語（統一感のためブラウン）
        }
        
        # 差分用カラーマップ作成
        self.difference_colormaps = {
            'difference_standard': ListedColormap([
                self.difference_colors['decrease_large'],
                self.difference_colors['decrease_medium'], 
                self.difference_colors['decrease_small'],
                self.difference_colors['common'],
                self.difference_colors['increase_small'],
                self.difference_colors['increase_medium'],
                self.difference_colors['increase_large']
            ]),
            'science_focused': ListedColormap([
                self.difference_colors['decrease_medium'],
                self.difference_colors['common'],
                self.difference_colors['increase_medium'],
                self.difference_colors['science_highlight']
            ])
        }
    
    def get_matplotlib_font_props(self, font_path):
        """matplotlib用フォントプロパティを取得"""
        # フォントパスが指定されている場合
        if font_path and Path(font_path).exists():
            try:
                return fm.FontProperties(fname=font_path)
            except Exception as e:
                logger.warning(f"フォント読み込み失敗: {e}")
        
        # デフォルトの日本語フォントを試す
        fonts_dir = self.base_generator.fonts_dir
        default_fonts = [
            fonts_dir / "ipaexg.ttf",
            fonts_dir / "ipag.ttf", 
            fonts_dir / "NotoSansJP-Regular.otf",
            fonts_dir / "HannariMincho-Regular.otf"
        ]
        
        for default_font in default_fonts:
            if default_font.exists():
                try:
                    logger.info(f"デフォルト日本語フォントを使用: {default_font}")
                    return fm.FontProperties(fname=str(default_font))
                except Exception as e:
                    logger.warning(f"デフォルトフォント読み込み失敗: {e}")
                    continue
        
        logger.warning("利用可能な日本語フォントが見つかりませんでした")
        return None
    
    def calculate_word_frequencies(self, text, excluded_words=None):
        """テキストから単語頻度を計算"""
        tokenized_text = self.base_generator.tokenize_japanese(text, excluded_words)
        words = tokenized_text.split()
        return Counter(words)
    
    def calculate_difference_statistics(self, base_freq, compare_freq):
        """差分統計を計算"""
        all_words = set(base_freq.keys()) | set(compare_freq.keys())
        
        statistics = {
            'total_words_base': len(base_freq),
            'total_words_compare': len(compare_freq),
            'unique_words_base': len(set(base_freq.keys())),
            'unique_words_compare': len(set(compare_freq.keys())),
            'new_words': [],      # 新出現語
            'lost_words': [],     # 消失語
            'increased_words': [],  # 増加語
            'decreased_words': [],  # 減少語
            'science_term_changes': {}  # 科学用語変化
        }
        
        for word in all_words:
            base_count = base_freq.get(word, 0)
            compare_count = compare_freq.get(word, 0)
            
            if base_count == 0 and compare_count > 0:
                statistics['new_words'].append((word, compare_count))
            elif base_count > 0 and compare_count == 0:
                statistics['lost_words'].append((word, base_count))
            elif compare_count > base_count:
                statistics['increased_words'].append((word, compare_count - base_count))
            elif compare_count < base_count:
                statistics['decreased_words'].append((word, base_count - compare_count))
        
        # 科学用語変化の分析
        for level, terms in self.science_terms.items():
            for term in terms:
                base_count = base_freq.get(term, 0)
                compare_count = compare_freq.get(term, 0)
                if base_count > 0 or compare_count > 0:
                    statistics['science_term_changes'][term] = {
                        'level': level,
                        'base': base_count,
                        'compare': compare_count,
                        'change': compare_count - base_count
                    }
        
        # ソート（頻度順）
        statistics['new_words'].sort(key=lambda x: x[1], reverse=True)
        statistics['lost_words'].sort(key=lambda x: x[1], reverse=True)
        statistics['increased_words'].sort(key=lambda x: x[1], reverse=True)
        statistics['decreased_words'].sort(key=lambda x: x[1], reverse=True)
        
        return statistics
    
    def generate_difference_frequencies(self, base_freq, compare_freq, config):
        """差分頻度辞書を生成（方向性重視版）"""
        all_words = set(base_freq.keys()) | set(compare_freq.keys())
        
        # 設定からパラメータ取得
        calculation_method = config.get('calculation_method', 'frequency_difference')
        min_occurrence = config.get('min_occurrence', 1)
        min_difference = config.get('min_difference', 0.01)
        
        # 分析用の詳細データも保存
        self.word_analysis = {}
        difference_freq = {}
        
        for word in all_words:
            base_count = base_freq.get(word, 0)
            compare_count = compare_freq.get(word, 0)
            
            # 最小出現回数フィルタ
            if max(base_count, compare_count) < min_occurrence:
                continue
            
            # 差分計算（方向性保持）
            if calculation_method == 'frequency_difference':
                diff = compare_count - base_count
            elif calculation_method == 'relative_difference':
                if base_count == 0:
                    diff = compare_count if compare_count > 0 else 0
                else:
                    diff = (compare_count - base_count) / base_count
            elif calculation_method == 'log_ratio':
                if base_count == 0 or compare_count == 0:
                    diff = compare_count - base_count
                else:
                    diff = math.log(compare_count / base_count)
            else:
                diff = compare_count - base_count
            
            # 最小差分フィルタ
            if abs(diff) >= min_difference:
                # 単語分析データ保存（方向性情報含む）
                self.word_analysis[word] = {
                    'diff': diff,
                    'base': base_count,
                    'compare': compare_count,
                    'direction': 'increase' if diff > 0 else 'decrease' if diff < 0 else 'stable',
                    'magnitude': abs(diff)
                }
                
                # 科学用語の特別処理
                is_science_term = False
                if config.get('science_highlight', False):
                    for level, terms in self.science_terms.items():
                        if word in terms:
                            self.word_analysis[word]['science_level'] = level
                            is_science_term = True
                            break
                
                # 方向性に基づく強調計算
                if calculation_method == 'frequency_difference':
                    # 新出現語は大幅強調、減少語は控えめ
                    if base_count == 0 and compare_count > 0:  # 新出現語
                        weight = compare_count * 3  # 3倍強調
                    elif compare_count == 0 and base_count > 0:  # 消失語
                        weight = base_count * 0.5  # 控えめ表示
                    else:
                        weight = abs(diff) * 2  # 通常の変化
                elif calculation_method == 'relative_difference':
                    # 相対変化率に基づく重み
                    if abs(diff) > 2.0:  # 200%以上の変化
                        weight = min(abs(diff) * 10, 100)  # 上限100
                    else:
                        weight = abs(diff) * 20
                else:  # log_ratio
                    weight = abs(diff) * 30
                
                # 科学用語の追加強調
                if is_science_term:
                    weight *= 1.5
                
                difference_freq[word] = max(weight, 1)  # 最小値1を保証
        
        return difference_freq
    
    def generate_difference_wordcloud(self, config):
        """差分ワードクラウド生成"""
        try:
            # データソース取得
            base_source = config.get('base_dataset', 'q2_before')
            compare_source = config.get('compare_dataset', 'q2_after')
            
            # テキスト取得
            base_text = self.base_generator.sample_texts.get(base_source, {}).get('text', '')
            compare_text = self.base_generator.sample_texts.get(compare_source, {}).get('text', '')
            
            if not base_text.strip() or not compare_text.strip():
                return None, "比較データが不足しています", {}
            
            # 除外単語設定
            excluded_words = set()
            if config.get('exclude_categories'):
                for category in config.get('exclude_categories', []):
                    if category in self.base_generator.category_stop_words:
                        excluded_words.update(self.base_generator.category_stop_words[category])
            
            if config.get('custom_exclude_words'):
                custom_words = [w.strip() for w in config.get('custom_exclude_words', '').split(',') if w.strip()]
                excluded_words.update(custom_words)
            
            # 単語頻度計算
            base_freq = self.calculate_word_frequencies(base_text, excluded_words)
            compare_freq = self.calculate_word_frequencies(compare_text, excluded_words)
            
            # 差分統計計算
            statistics = self.calculate_difference_statistics(base_freq, compare_freq)
            
            # 差分頻度辞書生成
            difference_freq = self.generate_difference_frequencies(base_freq, compare_freq, config)
            
            if not difference_freq:
                return None, "有意な差分が見つかりませんでした", statistics
            
            # 方向性に基づく色分け関数（アクセシブルカラー準拠）
            def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
                if not hasattr(self, 'word_analysis') or word not in self.word_analysis:
                    return self.difference_colors['common']  # デフォルト色
                
                analysis = self.word_analysis[word]
                direction = analysis['direction']
                magnitude = analysis['magnitude']
                
                # 科学用語の特別色（統一感のためブラウン）
                if 'science_level' in analysis:
                    return self.difference_colors['science_highlight']
                
                # 方向性に基づく色選択（アクセシブルカラー使用）
                if direction == 'increase':
                    if magnitude > 20:  # 大幅増加
                        return self.difference_colors['increase_large']
                    elif magnitude > 5:  # 中程度増加
                        return self.difference_colors['increase_medium']
                    else:  # 軽微増加
                        return self.difference_colors['increase_small']
                elif direction == 'decrease':
                    if magnitude > 20:  # 大幅減少
                        return self.difference_colors['decrease_large']
                    elif magnitude > 5:  # 中程度減少
                        return self.difference_colors['decrease_medium']
                    else:  # 軽微減少
                        return self.difference_colors['decrease_small']
                else:
                    return self.difference_colors['common']
            
            # ワードクラウド生成準備（スケーリング調整）
            max_freq = max(difference_freq.values()) if difference_freq else 1
            scale_factor = min(100, max(10, max_freq))
            freq_text = ' '.join([f"{word} " * int((freq / max_freq) * scale_factor) for word, freq in difference_freq.items()])
            
            # フォント設定
            font_key = config.get('font', 'default')
            font_info = self.base_generator.available_fonts.get(font_key, {})
            font_path = font_info.get('path')
            
            if font_path and not Path(font_path).is_absolute():
                font_path = str(project_root / font_path)
            
            # カラーマップ選択
            colormap_name = config.get('difference_colormap', 'difference_standard')
            colormap = self.difference_colormaps.get(colormap_name, self.difference_colormaps['difference_standard'])
            
            # ワードクラウド設定（固定パラメータ準拠）
            fixed_params = self.base_generator.FIXED_PARAMS
            wordcloud_config = {
                'width': config.get('width', 1000),
                'height': config.get('height', 600),
                'background_color': fixed_params['background_color'],  # 固定パラメータ
                'max_words': fixed_params['max_words'],                # 固定パラメータ
                'color_func': color_func,                              # カスタム色分け関数
                'relative_scaling': fixed_params['relative_scaling'],  # 固定パラメータ
                'min_font_size': fixed_params['min_font_size'],        # 固定パラメータ
                'max_font_size': fixed_params['max_font_size'],        # 固定パラメータ
                'prefer_horizontal': fixed_params['prefer_horizontal'], # 固定パラメータ
                'collocations': False,
                'stopwords': set()
            }
            
            if font_path:
                wordcloud_config['font_path'] = font_path
            
            # ワードクラウド生成
            wordcloud = WordCloud(**wordcloud_config).generate(freq_text)
            
            # 画像データ生成
            plt.figure(figsize=(12, 8))
            
            # matplotlib全体の日本語フォント設定
            font_props = self.get_matplotlib_font_props(font_path)
            if font_props:
                # タイトル専用でフォントプロパティを使用（rcParamsは使わない）
                pass  # font_propsをタイトルで直接使用
            
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            
            # 日本語タイトル設定（フォント指定）
            title_props = {'fontsize': 16, 'pad': 20}
            if font_props:
                title_props['fontproperties'] = font_props
            plt.title(f'差分分析: {base_source} → {compare_source}', **title_props)
            
            # Base64エンコード
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return img_base64, None, statistics
            
        except Exception as e:
            logger.error(f"差分ワードクラウド生成エラー: {e}")
            return None, f"生成エラー: {str(e)}", {}


class WordTreeGenerator:
    """Word Tree生成クラス（D3.js用データ準備）"""
    
    def __init__(self, base_generator):
        """ベースジェネレータから機能を継承"""
        self.base_generator = base_generator
        self.tokenizer = base_generator.tokenizer
        
        # 推奨ルート語（科学教育テーマ）
        self.recommended_roots = {
            'science': ['塩', 'ナトリウム', '塩化ナトリウム'],
            'experiment': ['炎色反応', '結晶', '実験'],
            'emotion': ['楽しかった', 'わかった', '面白い', 'すごい'],
            'action': ['見る', '観察', 'やる', '知る']
        }
    
    def tokenize_sentences(self, text):
        """テキストを文単位に分割"""
        # 句点で分割（。！？で区切る）
        import re
        sentences = re.split(r'[。！？]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_word_contexts(self, text, root_word, excluded_words=None):
        """ルート語の文脈を抽出"""
        sentences = self.tokenize_sentences(text)
        contexts = []
        
        for sentence in sentences:
            if root_word in sentence:
                # 文を単語に分割（除外語を適用）
                tokenized = self.base_generator.tokenize_japanese(sentence, excluded_words)
                words = tokenized.split()
                
                # ルート語の位置を見つけて文脈を抽出
                if root_word in words:
                    root_index = words.index(root_word)
                    
                    # 前後の文脈を取得
                    context = {
                        'sentence': sentence,
                        'words': words,
                        'root_index': root_index,
                        'before': words[:root_index],
                        'after': words[root_index + 1:]
                    }
                    contexts.append(context)
        
        return contexts
    
    def build_tree_structure(self, contexts, root_word, depth=3):
        """Word Tree用の階層構造を構築"""
        tree = {
            'word': root_word,
            'count': len(contexts),
            'children': defaultdict(lambda: {'count': 0, 'children': defaultdict(dict)})
        }
        
        for context in contexts:
            # 後続語の階層構造を構築
            after_words = context['after']
            current_level = tree['children']
            
            for i, word in enumerate(after_words[:depth]):
                if word not in current_level:
                    current_level[word] = {
                        'word': word,
                        'count': 0,
                        'children': defaultdict(dict) if i < depth - 1 else {}
                    }
                current_level[word]['count'] += 1
                current_level = current_level[word]['children'] if 'children' in current_level[word] else {}
        
        # defaultdictを通常のdictに変換
        def convert_to_dict(node):
            if isinstance(node, defaultdict):
                node = dict(node)
            if 'children' in node and node['children']:
                node['children'] = [convert_to_dict(child) for child in node['children'].values()]
            else:
                node['children'] = []
            return node
        
        tree['children'] = [convert_to_dict(child) for child in tree['children'].values()]
        
        return tree
    
    def generate_word_tree_data(self, config):
        """Word Tree用データ生成"""
        try:
            # データソース取得
            text_key = config.get('text_source', 'all_responses')
            if text_key == 'custom':
                text = config.get('custom_text', '')
            else:
                text = self.base_generator.sample_texts.get(text_key, {}).get('text', '')
            
            if not text.strip():
                return None, "テキストが空です", {}
            
            # 除外単語設定
            excluded_words = set()
            if config.get('exclude_categories'):
                for category in config.get('exclude_categories', []):
                    if category in self.base_generator.category_stop_words:
                        excluded_words.update(self.base_generator.category_stop_words[category])
            
            if config.get('custom_exclude_words'):
                custom_words = [w.strip() for w in config.get('custom_exclude_words', '').split(',') if w.strip()]
                excluded_words.update(custom_words)
            
            # ルート語選択（自動または手動）
            root_words = []
            if config.get('auto_select_roots', True):
                # 推奨ルート語から自動選択
                for category_words in self.recommended_roots.values():
                    for word in category_words:
                        if word in text:
                            root_words.append(word)
                            if len(root_words) >= config.get('max_roots', 3):
                                break
                    if len(root_words) >= config.get('max_roots', 3):
                        break
            else:
                # ユーザー指定のルート語
                custom_roots = config.get('custom_roots', '')
                if custom_roots:
                    root_words = [w.strip() for w in custom_roots.split(',') if w.strip()]
            
            if not root_words:
                return None, "ルート語が見つかりません", {}
            
            # 各ルート語についてツリー構造を生成
            trees = []
            for root_word in root_words[:config.get('max_roots', 3)]:
                contexts = self.extract_word_contexts(text, root_word, excluded_words)
                if contexts:
                    tree = self.build_tree_structure(
                        contexts, 
                        root_word, 
                        depth=config.get('tree_depth', 3)
                    )
                    trees.append(tree)
            
            # 統計情報
            statistics = {
                'root_words': root_words,
                'total_contexts': sum(tree['count'] for tree in trees),
                'trees': len(trees)
            }
            
            return trees, None, statistics
            
        except Exception as e:
            logger.error(f"Word Tree生成エラー: {e}")
            return None, f"生成エラー: {str(e)}", {}


class CooccurrenceNetworkGenerator:
    """共起ネットワーク生成クラス - シンプル版（既存ライブラリ活用）"""
    
    def __init__(self, base_generator):
        """ベースジェネレータから機能を継承"""
        self.base_generator = base_generator
        self.tokenizer = base_generator.tokenizer
        
        # ネットワーク可視化設定（アクセシブルカラー準拠）
        self.network_colors = {
            'node': {
                'default': self.base_generator.ACCESSIBLE_COLORS['blue'],
                'important': self.base_generator.ACCESSIBLE_COLORS['orange'],
                'science': self.base_generator.ACCESSIBLE_COLORS['brown']
            },
            'edge': {
                'weak': '#cccccc',
                'medium': '#888888',
                'strong': '#444444'
            }
        }
    
    def _tokenize_sentences(self, text):
        """テキストを文単位に分割"""
        import re
        sentences = re.split(r'[。！？]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def calculate_cooccurrence_matrix(self, text, excluded_words=None):
        """scikit-learn活用で共起行列を効率的に計算"""
        sentences = self._tokenize_sentences(text)
        
        # 各文を単語に分割（除外語適用）
        processed_sentences = []
        for sentence in sentences:
            tokenized = self.base_generator.tokenize_japanese(sentence, excluded_words)
            if tokenized.strip():
                processed_sentences.append(tokenized)
        
        if not processed_sentences:
            return None, None, None
        
        # CountVectorizerで語彙ベクトル化
        vectorizer = CountVectorizer(
            lowercase=False,
            stop_words=None,  # 既に除外済み
            min_df=2,         # 最低2回出現
            max_features=100  # 上位100語まで
        )
        
        try:
            X = vectorizer.fit_transform(processed_sentences)
            # 共起行列 = X^T * X（効率的な疎行列計算）
            cooccurrence_matrix = (X.T @ X).toarray()
            words = vectorizer.get_feature_names_out()
            word_freq = dict(zip(words, X.sum(axis=0).A1))
            
            return cooccurrence_matrix, words, word_freq
            
        except ValueError as e:
            logger.warning(f"共起行列計算でエラー: {e}")
            return None, None, None
    
    def build_network_graph(self, cooccurrence_matrix, words, word_freq, config):
        """NetworkXで直接グラフ構築"""
        # NetworkXで共起行列から直接グラフ作成
        G = nx.from_numpy_array(cooccurrence_matrix)
        
        # ノードラベルを単語に設定
        mapping = {i: word for i, word in enumerate(words)}
        G = nx.relabel_nodes(G, mapping)
        
        # ノード属性設定（頻度情報）
        for word in words:
            if word in word_freq:
                G.nodes[word]['frequency'] = word_freq[word]
        
        # 閾値でエッジフィルタリング（NetworkX組み込み機能）
        min_edge_weight = config.get('min_edge_weight', 2)
        edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) 
                          if d['weight'] < min_edge_weight]
        G.remove_edges_from(edges_to_remove)
        
        # 孤立ノード削除
        isolated = list(nx.isolates(G))
        G.remove_nodes_from(isolated)
        
        # ノード数制限
        max_nodes = config.get('max_nodes', 30)
        if G.number_of_nodes() > max_nodes:
            # 重要度順（次数×頻度）でノード選択
            node_importance = {
                node: G.degree(node) * G.nodes[node].get('frequency', 1)
                for node in G.nodes()
            }
            important_nodes = sorted(node_importance.items(), 
                                   key=lambda x: x[1], reverse=True)[:max_nodes]
            nodes_to_keep = [node for node, _ in important_nodes]
            nodes_to_remove = [node for node in G.nodes() if node not in nodes_to_keep]
            G.remove_nodes_from(nodes_to_remove)
        
        return G
    
    def get_matplotlib_font_props(self, font_path):
        """matplotlib用フォントプロパティを取得"""
        # フォントパスが指定されている場合
        if font_path and Path(font_path).exists():
            try:
                logger.info(f"指定フォントを使用: {font_path}")
                return fm.FontProperties(fname=font_path)
            except Exception as e:
                logger.warning(f"指定フォント読み込み失敗: {e}")
        
        # デフォルトの日本語フォント（はんなり明朝を優先）
        fonts_dir = self.base_generator.fonts_dir
        default_fonts = [
            fonts_dir / "HannariMincho-Regular.otf",  # はんなり明朝を優先
            fonts_dir / "ipaexg.ttf",
            fonts_dir / "ipag.ttf", 
            fonts_dir / "NotoSansJP-Regular.otf"
        ]
        
        for default_font in default_fonts:
            if default_font.exists():
                try:
                    logger.info(f"デフォルト日本語フォントを使用: {default_font}")
                    return fm.FontProperties(fname=str(default_font))
                except Exception as e:
                    logger.warning(f"デフォルトフォント読み込み失敗: {e}")
                    continue
        
        logger.warning("利用可能な日本語フォントが見つかりませんでした")
        return None
    
    def generate_cooccurrence_image(self, config):
        """共起ネットワーク静的画像生成（wordcloudと同じインターフェース）"""
        try:
            # データソース取得
            text_key = config.get('text_source', 'all_responses')
            if text_key == 'custom':
                text = config.get('custom_text', '')
            else:
                text = self.base_generator.sample_texts.get(text_key, {}).get('text', '')
            
            if not text.strip():
                return None, "テキストが空です", {}
            
            # 除外単語設定
            excluded_words = set()
            if config.get('exclude_categories'):
                for category in config.get('exclude_categories', []):
                    if category in self.base_generator.category_stop_words:
                        excluded_words.update(self.base_generator.category_stop_words[category])
            
            if config.get('custom_exclude_words'):
                custom_words = [w.strip() for w in config.get('custom_exclude_words', '').split(',') if w.strip()]
                excluded_words.update(custom_words)
            
            # Step 1: scikit-learn共起行列計算
            cooccurrence_matrix, words, word_freq = self.calculate_cooccurrence_matrix(text, excluded_words)
            
            if cooccurrence_matrix is None:
                return None, "共起関係が見つかりませんでした", {}
            
            # Step 2: NetworkXグラフ構築
            G = self.build_network_graph(cooccurrence_matrix, words, word_freq, config)
            
            if G.number_of_nodes() == 0:
                return None, "表示可能なネットワークが見つかりませんでした", {}
            
            # Step 3: matplotlib描画設定
            plt.figure(figsize=(config.get('width', 800)/100, config.get('height', 600)/100))
            
            # レイアウト計算
            layout_type = config.get('layout', 'spring')
            if layout_type == 'spring':
                pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            elif layout_type == 'circular':
                pos = nx.circular_layout(G)
            elif layout_type == 'kamada_kawai':
                pos = nx.kamada_kawai_layout(G)
            else:
                pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            
            # ノード色・サイズ設定
            node_colors = []
            node_sizes = []
            max_freq = max(word_freq.values()) if word_freq else 1
            
            for node in G.nodes():
                freq = G.nodes[node].get('frequency', 1)
                
                # 科学用語判定
                is_science = any(node in terms for terms in [
                    ['塩', '食塩', '塩分'],
                    ['ナトリウム', '塩化ナトリウム'],
                    ['Na', 'NaCl', 'イオン', 'Na+']
                ])
                
                # 重要語判定（頻度上位20%）
                is_important = freq >= max_freq * 0.8
                
                # 色設定
                if is_science:
                    node_colors.append(self.network_colors['node']['science'])
                elif is_important:
                    node_colors.append(self.network_colors['node']['important'])
                else:
                    node_colors.append(self.network_colors['node']['default'])
                
                # サイズ設定（100-1000の範囲）
                size = 100 + (freq / max_freq) * 900
                node_sizes.append(size)
            
            # エッジ幅設定
            edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
            if edge_weights:
                max_weight = max(edge_weights)
                min_weight = min(edge_weights)
                edge_widths = [1 + 4 * (w - min_weight) / (max_weight - min_weight) 
                              if max_weight > min_weight else 2.5 
                              for w in edge_weights]
            else:
                edge_widths = [2.5] * G.number_of_edges()
            
            # フォント設定（はんなり明朝を優先使用）
            font_key = config.get('font', 'hannari')  # デフォルトをはんなり明朝に
            
            # はんなり明朝を優先的に選択
            if font_key in ['default', 'hannari'] or font_key not in self.base_generator.available_fonts:
                hannari_path = self.base_generator.fonts_dir / "HannariMincho-Regular.otf"
                if hannari_path.exists():
                    font_path = str(hannari_path)
                    logger.info(f"はんなり明朝を使用します: {font_path}")
                else:
                    font_info = self.base_generator.available_fonts.get(font_key, {})
                    font_path = font_info.get('path')
                    if font_path and not Path(font_path).is_absolute():
                        font_path = str(project_root / font_path)
            else:
                font_info = self.base_generator.available_fonts.get(font_key, {})
                font_path = font_info.get('path')
                if font_path and not Path(font_path).is_absolute():
                    font_path = str(project_root / font_path)
            
            font_props = self.get_matplotlib_font_props(font_path)
            font_family = font_props.get_name() if font_props else 'sans-serif'
            logger.info(f"使用フォントファミリー: {font_family}")
            
            # ネットワーク描画
            plt.clf()
            plt.figure(figsize=(config.get('width', 800)/100, config.get('height', 600)/100))
            
            # 背景色設定
            background_color = config.get('background_color', '#f8f8f8')
            plt.gca().set_facecolor(background_color)
            
            # エッジ描画
            nx.draw_networkx_edges(G, pos, 
                                 width=edge_widths,
                                 edge_color='#888888',
                                 alpha=0.6)
            
            # ノード描画
            nx.draw_networkx_nodes(G, pos,
                                 node_color=node_colors,
                                 node_size=node_sizes,
                                 alpha=0.8)
            
            # ラベル描画（日本語フォント対応）
            # NetworkXのlabels描画は日本語フォントをサポートしないため、個別描画
            font_size = config.get('font_size', 12)
            for node, (x, y) in pos.items():
                # 個別にラベルを描画（fontpropertiesを直接指定）
                text_props = {
                    'ha': 'center',
                    'va': 'center', 
                    'fontsize': font_size,
                    'weight': 'bold',
                    'color': 'black'
                }
                
                # 日本語フォントが利用可能な場合は指定
                if font_props:
                    text_props['fontproperties'] = font_props
                
                plt.text(x, y, str(node), **text_props)
            
            plt.axis('off')
            plt.tight_layout()
            
            # 統計情報（JSONシリアライゼーション対応）
            statistics = {
                'total_nodes': int(G.number_of_nodes()),
                'total_edges': int(G.number_of_edges()),
                'density': float(nx.density(G)) if G.number_of_nodes() > 0 else 0.0,
                'components': int(nx.number_connected_components(G)),
                'max_frequency': int(max_freq),
                'layout_used': str(layout_type)
            }
            
            # Base64エンコード（wordcloudと同じ）
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150,
                       facecolor=background_color, edgecolor='none')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return img_base64, None, statistics
            
        except Exception as e:
            logger.error(f"共起ネットワーク画像生成エラー: {e}")
            return None, f"生成エラー: {str(e)}", {}

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
difference_generator = DifferenceWordCloudGenerator(generator)
word_tree_generator = WordTreeGenerator(generator)
cooccurrence_generator = CooccurrenceNetworkGenerator(generator)

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

@app.route('/api/difference-generate', methods=['POST'])
def generate_difference_wordcloud():
    """差分ワードクラウド生成API"""
    try:
        config = request.json
        
        img_base64, error, statistics = difference_generator.generate_difference_wordcloud(config)
        
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'statistics': statistics
            }), 400
        
        return jsonify({
            'success': True,
            'image': img_base64,
            'config': config,
            'statistics': statistics,
            'type': 'difference'
        })
        
    except Exception as e:
        logger.error(f"差分API エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'statistics': {}
        }), 500

@app.route('/api/difference-colormaps')
def get_difference_colormaps():
    """差分用カラーマップ取得"""
    return jsonify({
        'colormaps': list(difference_generator.difference_colormaps.keys()),
        'colors': difference_generator.difference_colors
    })

@app.route('/api/science-terms')
def get_science_terms():
    """科学用語リスト取得"""
    return jsonify({
        'science_terms': difference_generator.science_terms
    })

@app.route('/api/word-tree-generate', methods=['POST'])
def generate_word_tree():
    """Word Tree生成API"""
    try:
        config = request.json
        
        trees, error, statistics = word_tree_generator.generate_word_tree_data(config)
        
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'statistics': statistics
            }), 400
        
        return jsonify({
            'success': True,
            'trees': trees,
            'statistics': statistics,
            'type': 'word_tree'
        })
        
    except Exception as e:
        logger.error(f"Word Tree API エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'statistics': {}
        }), 500

@app.route('/api/recommended-roots')
def get_recommended_roots():
    """推奨ルート語取得"""
    return jsonify({
        'recommended_roots': word_tree_generator.recommended_roots
    })

@app.route('/api/network-layouts')
def get_network_layouts():
    """共起ネットワーク用レイアウト一覧"""
    return jsonify({
        'layouts': {
            'spring': {
                'name': 'バネモデル',
                'description': '自然なクラスタ配置（推奨）'
            },
            'circular': {
                'name': '円形配置',
                'description': 'ノードを円形に配置'
            },
            'kamada_kawai': {
                'name': '力学モデル',
                'description': '物理シミュレーションベース'
            }
        },
        'default_config': {
            'layout': 'spring',
            'min_edge_weight': 2,
            'max_nodes': 30,
            'font_size': 10,
            'width': 800,
            'height': 600,
            'background_color': '#f8f8f8'
        }
    })

@app.route('/api/cooccurrence-generate', methods=['POST'])
def generate_cooccurrence_network():
    """共起ネットワーク画像生成API（wordcloudと同じインターフェース）"""
    try:
        config = request.json
        
        img_base64, error, statistics = cooccurrence_generator.generate_cooccurrence_image(config)
        
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'statistics': statistics
            }), 400
        
        return jsonify({
            'success': True,
            'image': img_base64,  # wordcloudと同じフォーマット
            'statistics': statistics,
            'config': config,
            'type': 'cooccurrence_network'
        })
        
    except Exception as e:
        logger.error(f"共起ネットワーク API エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'statistics': {}
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
    print("🔍 新機能: 共起ネットワーク静的画像生成（scikit-learn + NetworkX活用）")
    print("=" * 60)
    
    # Flaskアプリ実行（ポート5002）
    app.run(debug=True, host='0.0.0.0', port=5002)