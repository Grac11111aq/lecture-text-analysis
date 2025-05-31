#!/usr/bin/env python3
"""
感情・興味分析システム
東京高専出前授業効果測定プロジェクト

主要機能:
1. 感想文の感情極性分析
2. 興味関心語彙の抽出・定量化
3. ワードクラウド生成（全体・クラス別）
4. 実験別フィードバック分析

実行方法: python scripts/analysis/04_sentiment_analysis.py
"""

import sys
import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import re
from wordcloud import WordCloud
import json

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

class SentimentAnalyzer:
    """感情・興味分析クラス"""
    
    def __init__(self, config_path="config/analysis_config.yaml"):
        """初期化"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.results = {}
        
        # 興味関心語彙の定義
        self.interest_keywords = {
            'positive': ['おもしろい', '面白い', 'すごい', 'きれい', '美しい', '楽しい', 'たのしい'],
            'engagement': ['びっくり', 'おどろき', '感動', '発見', '気づき', 'わかった'],
            'learning': ['理解', '学習', '勉強', '知識', '分かった', 'わかりました']
        }
        
        # 実験関連語彙
        self.experiment_keywords = {
            'flame_reaction': ['炎色反応', '炎の色', '火の色', '色が変わる', '緑色', '赤色', '炎'],
            'recrystallization': ['再結晶', '結晶', 'かたまる', '固まる', '氷みたい', '結晶化'],
            'general': ['実験', '観察', 'スケッチ', 'シャーレ', '試験管']
        }
        
    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/sentiment_analysis.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
        
    def _load_config(self, config_path):
        """設定ファイル読み込み"""
        return {
            'polarity_threshold': 0.1,
            'wordcloud_max_words': 100,
            'font_size': 12
        }
    
    def load_data(self):
        """データ読み込み"""
        self.logger.info("感想コメントデータ読み込み開始")
        
        try:
            # コメントデータ読み込み
            self.comments_data = pd.read_csv(
                'data/raw/comments.csv',
                encoding='utf-8'
            )
            
            self.logger.info(f"Comments data: {len(self.comments_data)} records")
            
            # データ検証
            self._validate_data()
            
        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {e}")
            raise
    
    def _validate_data(self):
        """データ検証"""
        required_cols = ['Page_ID', 'class']
        
        # テキスト列の特定
        text_cols = [col for col in self.comments_data.columns 
                    if 'comment' in col.lower() or 'text' in col.lower()]
        
        if not text_cols:
            # 全列をチェックしてテキスト列を推定
            for col in self.comments_data.columns:
                if col not in required_cols:
                    text_cols.append(col)
                    break
        
        if text_cols:
            self.text_column = text_cols[0]
            self.logger.info(f"使用するテキスト列: {self.text_column}")
        else:
            raise ValueError("テキスト列が見つかりません")
        
        # 基本統計
        self.logger.info(f"データサイズ: {self.comments_data.shape}")
        class_dist = self.comments_data['class'].value_counts()
        self.logger.info(f"クラス分布: {class_dist.to_dict()}")
    
    def extract_interest_features(self, text_data):
        """興味関心特徴量抽出"""
        features = defaultdict(list)
        
        for text in text_data:
            if pd.isna(text):
                for category in self.interest_keywords:
                    features[category].append(0)
                continue
                
            text_str = str(text).lower()
            
            # 各カテゴリの語彙出現回数カウント
            for category, keywords in self.interest_keywords.items():
                count = sum(len(re.findall(keyword, text_str)) for keyword in keywords)
                features[category].append(count)
        
        return dict(features)
    
    def extract_experiment_features(self, text_data):
        """実験関連特徴量抽出"""
        features = defaultdict(list)
        
        for text in text_data:
            if pd.isna(text):
                for category in self.experiment_keywords:
                    features[category].append(0)
                continue
                
            text_str = str(text).lower()
            
            # 各実験タイプの語彙出現回数カウント
            for category, keywords in self.experiment_keywords.items():
                count = sum(len(re.findall(keyword, text_str)) for keyword in keywords)
                features[category].append(count)
        
        return dict(features)
    
    def sentiment_analysis(self):
        """感情分析実行"""
        self.logger.info("感情分析開始")
        
        # 興味関心分析
        interest_features = self.extract_interest_features(self.comments_data[self.text_column])
        
        # 実験関連分析
        experiment_features = self.extract_experiment_features(self.comments_data[self.text_column])
        
        # 結果集約
        sentiment_results = {
            'interest_analysis': self._calculate_interest_rates(interest_features),
            'experiment_analysis': self._calculate_experiment_rates(experiment_features),
            'overall_sentiment': self._calculate_overall_sentiment()
        }
        
        self.results['sentiment'] = sentiment_results
        return sentiment_results
    
    def _calculate_interest_rates(self, features):
        """興味関心語彙使用率計算"""
        results = {}
        total_texts = len(self.comments_data)
        
        for category, counts in features.items():
            usage_rate = sum(1 for c in counts if c > 0) / total_texts
            total_mentions = sum(counts)
            avg_per_text = np.mean(counts)
            
            results[category] = {
                'usage_rate': usage_rate,
                'total_mentions': total_mentions,
                'avg_per_text': avg_per_text,
                'max_mentions': max(counts),
                'distribution': counts
            }
        
        return results
    
    def _calculate_experiment_rates(self, features):
        """実験関連語彙使用率計算"""
        results = {}
        total_texts = len(self.comments_data)
        
        for category, counts in features.items():
            usage_rate = sum(1 for c in counts if c > 0) / total_texts
            total_mentions = sum(counts)
            
            results[category] = {
                'usage_rate': usage_rate,
                'total_mentions': total_mentions,
                'avg_per_text': np.mean(counts)
            }
        
        return results
    
    def _calculate_overall_sentiment(self):
        """全体的感情傾向計算"""
        # 簡易的な感情スコア計算
        positive_words = ['おもしろい', '面白い', 'すごい', '楽しい', 'きれい']
        negative_words = ['つまらない', '難しい', 'わからない']
        
        sentiment_scores = []
        
        for text in self.comments_data[self.text_column]:
            if pd.isna(text):
                sentiment_scores.append(0)
                continue
                
            text_str = str(text).lower()
            positive_count = sum(len(re.findall(word, text_str)) for word in positive_words)
            negative_count = sum(len(re.findall(word, text_str)) for word in negative_words)
            
            score = positive_count - negative_count
            sentiment_scores.append(score)
        
        return {
            'mean_sentiment': np.mean(sentiment_scores),
            'positive_ratio': sum(1 for s in sentiment_scores if s > 0) / len(sentiment_scores),
            'neutral_ratio': sum(1 for s in sentiment_scores if s == 0) / len(sentiment_scores),
            'negative_ratio': sum(1 for s in sentiment_scores if s < 0) / len(sentiment_scores),
            'sentiment_distribution': sentiment_scores
        }
    
    def generate_wordclouds(self):
        """ワードクラウド生成"""
        self.logger.info("ワードクラウド生成開始")
        
        # 出力ディレクトリ確保
        output_dir = Path('outputs/wordclouds')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 全体ワードクラウド
        self._generate_overall_wordcloud(output_dir)
        
        # クラス別ワードクラウド
        self._generate_class_wordclouds(output_dir)
        
        self.logger.info("ワードクラウド生成完了")
    
    def _generate_overall_wordcloud(self, output_dir):
        """全体ワードクラウド生成"""
        # 全テキスト結合
        all_text = ' '.join(self.comments_data[self.text_column].dropna().astype(str))
        
        # ワードクラウド生成
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=100,
            colormap='viridis',
            font_path=None  # システムフォント使用
        ).generate(all_text)
        
        # 保存
        plt.figure(figsize=(12, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('全体ワードクラウド', fontsize=16, pad=20)
        plt.tight_layout()
        plt.savefig(output_dir / 'overall_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_class_wordclouds(self, output_dir):
        """クラス別ワードクラウド生成"""
        classes = self.comments_data['class'].unique()
        
        for class_id in classes:
            if pd.isna(class_id):
                continue
                
            class_data = self.comments_data[self.comments_data['class'] == class_id]
            
            if len(class_data) == 0:
                continue
            
            # クラス別テキスト結合
            class_text = ' '.join(class_data[self.text_column].dropna().astype(str))
            
            if not class_text.strip():
                continue
                
            # ワードクラウド生成
            wordcloud = WordCloud(
                width=600,
                height=400,
                background_color='white',
                max_words=50,
                colormap='Set2'
            ).generate(class_text)
            
            # 保存
            plt.figure(figsize=(10, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title(f'クラス {class_id} ワードクラウド', fontsize=14, pad=20)
            plt.tight_layout()
            plt.savefig(output_dir / f'class_{class_id}_wordcloud.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def create_visualizations(self):
        """可視化作成"""
        self.logger.info("可視化作成開始")
        
        # 出力ディレクトリ確保
        output_dir = Path('outputs/sentiment_results')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 興味関心分析結果の可視化
        self._visualize_interest_analysis(output_dir)
        
        # 実験関連分析結果の可視化
        self._visualize_experiment_analysis(output_dir)
        
        # 感情分析結果の可視化
        self._visualize_sentiment_distribution(output_dir)
        
        self.logger.info("可視化作成完了")
    
    def _visualize_interest_analysis(self, output_dir):
        """興味関心分析可視化"""
        if 'sentiment' not in self.results:
            return
            
        interest_data = self.results['sentiment']['interest_analysis']
        
        # 使用率バープロット
        categories = list(interest_data.keys())
        usage_rates = [interest_data[cat]['usage_rate'] for cat in categories]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, usage_rates, color=['skyblue', 'lightgreen', 'lightcoral'])
        plt.ylabel('使用率')
        plt.title('興味関心語彙の使用率')
        plt.xticks(rotation=45)
        
        # 値表示
        for bar, rate in zip(bars, usage_rates):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{rate:.1%}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'interest_usage_rates.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _visualize_experiment_analysis(self, output_dir):
        """実験関連分析可視化"""
        if 'sentiment' not in self.results:
            return
            
        experiment_data = self.results['sentiment']['experiment_analysis']
        
        # 使用率バープロット
        categories = list(experiment_data.keys())
        usage_rates = [experiment_data[cat]['usage_rate'] for cat in categories]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, usage_rates, color=['gold', 'orange', 'lightblue'])
        plt.ylabel('使用率')
        plt.title('実験関連語彙の使用率')
        plt.xticks(rotation=45)
        
        # 値表示
        for bar, rate in zip(bars, usage_rates):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{rate:.1%}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'experiment_usage_rates.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _visualize_sentiment_distribution(self, output_dir):
        """感情分布可視化"""
        if 'sentiment' not in self.results:
            return
            
        sentiment_data = self.results['sentiment']['overall_sentiment']
        
        # 感情分布パイチャート
        labels = ['ポジティブ', 'ニュートラル', 'ネガティブ']
        sizes = [
            sentiment_data['positive_ratio'],
            sentiment_data['neutral_ratio'],
            sentiment_data['negative_ratio']
        ]
        colors = ['lightgreen', 'lightgray', 'lightcoral']
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('感情分布', fontsize=16)
        plt.axis('equal')
        plt.savefig(output_dir / 'sentiment_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(self):
        """結果保存"""
        self.logger.info("結果保存開始")
        
        # 出力ディレクトリ確保
        output_dir = Path('outputs/sentiment_results')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON形式で保存
        with open(output_dir / 'sentiment_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # CSV形式でサマリー保存
        if 'sentiment' in self.results:
            self._save_summary_csv(output_dir)
        
        self.logger.info("結果保存完了")
    
    def _save_summary_csv(self, output_dir):
        """サマリーCSV保存"""
        summary_data = []
        
        # 興味関心データ
        for category, data in self.results['sentiment']['interest_analysis'].items():
            summary_data.append({
                'type': 'interest',
                'category': category,
                'usage_rate': data['usage_rate'],
                'total_mentions': data['total_mentions'],
                'avg_per_text': data['avg_per_text']
            })
        
        # 実験関連データ
        for category, data in self.results['sentiment']['experiment_analysis'].items():
            summary_data.append({
                'type': 'experiment',
                'category': category,
                'usage_rate': data['usage_rate'],
                'total_mentions': data['total_mentions'],
                'avg_per_text': data['avg_per_text']
            })
        
        # CSV保存
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(output_dir / 'sentiment_summary.csv', index=False, encoding='utf-8')
    
    def run_analysis(self):
        """分析実行"""
        self.logger.info("感情・興味分析開始")
        
        try:
            # データ読み込み
            self.load_data()
            
            # 感情分析
            self.sentiment_analysis()
            
            # ワードクラウド生成
            self.generate_wordclouds()
            
            # 可視化作成
            self.create_visualizations()
            
            # 結果保存
            self.save_results()
            
            # 結果要約表示
            self._print_summary()
            
            self.logger.info("感情・興味分析完了")
            
        except Exception as e:
            self.logger.error(f"分析エラー: {e}")
            raise
    
    def _print_summary(self):
        """結果要約表示"""
        print("\n" + "="*60)
        print("感情・興味分析結果要約")
        print("="*60)
        
        if 'sentiment' not in self.results:
            print("分析結果なし")
            return
        
        # 興味関心分析
        print("\n【興味関心分析】")
        for category, data in self.results['sentiment']['interest_analysis'].items():
            print(f"  {category}: 使用率={data['usage_rate']:.1%}, 総言及数={data['total_mentions']}")
        
        # 実験関連分析
        print("\n【実験関連分析】")
        for category, data in self.results['sentiment']['experiment_analysis'].items():
            print(f"  {category}: 使用率={data['usage_rate']:.1%}, 総言及数={data['total_mentions']}")
        
        # 全体感情
        overall = self.results['sentiment']['overall_sentiment']
        print(f"\n【全体感情】")
        print(f"  ポジティブ: {overall['positive_ratio']:.1%}")
        print(f"  ニュートラル: {overall['neutral_ratio']:.1%}")
        print(f"  ネガティブ: {overall['negative_ratio']:.1%}")
        print(f"  平均感情スコア: {overall['mean_sentiment']:.2f}")


if __name__ == "__main__":
    # ログディレクトリ確保
    Path('logs').mkdir(exist_ok=True)
    
    # 分析実行
    analyzer = SentimentAnalyzer()
    analyzer.run_analysis()