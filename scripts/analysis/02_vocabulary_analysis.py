#!/usr/bin/env python3
"""
語彙変化分析システム
東京高専出前授業効果測定プロジェクト

主要機能:
1. 科学語彙の抽出・分類（みそ→塩→ナトリウム）
2. Before/After使用率比較・統計検定
3. クラス間差異分析
4. 効果量算出・可視化

実行方法: python scripts/analysis/02_vocabulary_analysis.py
"""

import sys
import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import json
from collections import defaultdict, Counter
import re

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

# 設定・ユーティリティ読み込み（作成後）
# from scripts.utils.data_loader import DataLoader
# from scripts.utils.text_preprocessor import TextPreprocessor  
# from scripts.utils.visualization_utils import VisualizationUtils


class VocabularyAnalyzer:
    """科学語彙変化分析クラス"""
    
    def __init__(self, config_path="config/analysis_config.yaml"):
        """初期化"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.results = {}
        
        # 分析対象語彙の定義
        self.target_vocabularies = {
            'basic_food': ['みそ', 'みそ汁', 'みそしる'],
            'basic_salt': ['塩', '食塩', '塩分'],
            'scientific': ['ナトリウム', '塩化ナトリウム', 'Na'],
            'advanced': ['Na+', 'NaCl', 'イオン']
        }
        
        # クラス情報
        self.classes = [1.0, 2.0, 3.0, 4.0]
        
    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/vocabulary_analysis.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
        
    def _load_config(self, config_path):
        """設定ファイル読み込み（YAML対応後に実装）"""
        # 暫定的なデフォルト設定
        return {
            'significance_level': 0.05,
            'effect_size_threshold': 0.2,
            'confidence_interval': 0.95,
            'multiple_comparison': 'bonferroni'
        }
    
    def load_data(self):
        """データ読み込み・前処理"""
        self.logger.info("データ読み込み開始")
        
        try:
            # Before データ
            self.before_data = pd.read_csv(
                'data/raw/q2_reasons_before.csv',
                encoding='utf-8'
            )
            
            # After データ  
            self.after_data = pd.read_csv(
                'data/raw/q2_reasons_after.csv',
                encoding='utf-8'
            )
            
            self.logger.info(f"Before data: {len(self.before_data)} records")
            self.logger.info(f"After data: {len(self.after_data)} records")
            
            # データ品質確認
            self._validate_data()
            
        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {e}")
            raise
    
    def _validate_data(self):
        """データ品質確認"""
        # 必須カラムの確認
        required_cols = ['Page_ID', 'class', 'Q2_MisoSalty_Reason']
        
        for df_name, df in [('before', self.before_data), ('after', self.after_data)]:
            # カラム名の正規化（差異対応）
            if 'Q2_MisoSaltyReason' in df.columns:
                df.rename(columns={'Q2_MisoSaltyReason': 'Q2_MisoSalty_Reason'}, inplace=True)
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"{df_name}データに必須カラムなし: {missing_cols}")
            
            # 欠損値確認
            null_counts = df[required_cols].isnull().sum()
            if null_counts.any():
                self.logger.warning(f"{df_name}データ欠損値: {null_counts.to_dict()}")
            
            # クラス分布確認
            class_dist = df['class'].value_counts()
            self.logger.info(f"{df_name}データクラス分布: {class_dist.to_dict()}")
    
    def extract_vocabulary_features(self, text_data):
        """語彙特徴量抽出"""
        features = defaultdict(list)
        
        for text in text_data:
            if pd.isna(text):
                # 欠損値の場合は全てFalse
                for category in self.target_vocabularies:
                    features[category].append(False)
                continue
                
            text_str = str(text).lower()
            
            # 各カテゴリの語彙使用チェック
            for category, vocab_list in self.target_vocabularies.items():
                contains_vocab = any(vocab in text_str for vocab in vocab_list)
                features[category].append(contains_vocab)
        
        return dict(features)
    
    def calculate_usage_rates(self, data, group_col='class'):
        """語彙使用率計算"""
        # テキスト列名を動的に決定（Before/Afterで異なるため）
        if 'Q2_MisoSalty_Reason' in data.columns:
            text_column = 'Q2_MisoSalty_Reason'  # Before データ
        elif 'Q2_MisoSaltyReason' in data.columns:
            text_column = 'Q2_MisoSaltyReason'   # After データ
        else:
            raise ValueError(f"理由テキスト列が見つかりません。利用可能な列: {list(data.columns)}")
        
        self.logger.info(f"使用するテキスト列: {text_column}")
        
        # 語彙特徴量抽出
        vocab_features = self.extract_vocabulary_features(data[text_column])
        
        # データフレーム化
        feature_df = pd.DataFrame(vocab_features)
        feature_df[group_col] = data[group_col].values
        
        # 使用率計算
        usage_rates = {}
        
        # 全体使用率
        overall_rates = {}
        for category in self.target_vocabularies:
            overall_rates[category] = feature_df[category].mean()
        usage_rates['overall'] = overall_rates
        
        # クラス別使用率
        class_rates = {}
        for class_id in self.classes:
            class_data = feature_df[feature_df[group_col] == class_id]
            if len(class_data) > 0:
                class_rates[f'class_{class_id}'] = {}
                for category in self.target_vocabularies:
                    class_rates[f'class_{class_id}'][category] = class_data[category].mean()
        usage_rates['by_class'] = class_rates
        
        return usage_rates, feature_df
    
    def statistical_testing(self, before_features, after_features):
        """統計的検定実行"""
        self.logger.info("統計的検定開始")
        
        test_results = {}
        
        # 各語彙カテゴリについて検定
        for category in self.target_vocabularies:
            self.logger.info(f"検定実行中: {category}")
            
            before_usage = before_features[category].astype(int)
            after_usage = after_features[category].astype(int)
            
            # Mann-Whitney U検定（独立群比較）
            statistic, pvalue = stats.mannwhitneyu(
                after_usage, before_usage, alternative='two-sided'
            )
            
            # 効果量計算（Cohen's d）
            effect_size = self._calculate_cohens_d(
                after_usage.mean(), before_usage.mean(),
                after_usage.std(), before_usage.std(),
                len(after_usage), len(before_usage)
            )
            
            # 信頼区間計算
            ci_lower, ci_upper = self._calculate_confidence_interval(
                after_usage, before_usage
            )
            
            test_results[category] = {
                'mann_whitney_u': float(statistic),
                'p_value': float(pvalue),
                'effect_size_cohens_d': float(effect_size),
                'confidence_interval': [float(ci_lower), float(ci_upper)],
                'before_mean': float(before_usage.mean()),
                'after_mean': float(after_usage.mean()),
                'before_std': float(before_usage.std()),
                'after_std': float(after_usage.std()),
                'sample_size_before': int(len(before_usage)),
                'sample_size_after': int(len(after_usage))
            }
            
        return test_results
    
    def _calculate_cohens_d(self, mean1, mean2, std1, std2, n1, n2):
        """Cohen's d効果量計算"""
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        if pooled_std == 0:
            return 0
        return (mean1 - mean2) / pooled_std
    
    def _calculate_confidence_interval(self, group1, group2, confidence=0.95):
        """信頼区間計算"""
        alpha = 1 - confidence
        
        # 平均値の差
        diff_mean = group1.mean() - group2.mean()
        
        # 標準誤差
        se = np.sqrt(group1.var()/len(group1) + group2.var()/len(group2))
        
        # t分布の臨界値
        df = len(group1) + len(group2) - 2
        t_critical = stats.t.ppf(1 - alpha/2, df)
        
        # 信頼区間
        margin = t_critical * se
        return diff_mean - margin, diff_mean + margin
    
    def class_comparison_analysis(self, before_features, after_features):
        """クラス間比較分析"""
        self.logger.info("クラス間比較分析開始")
        
        comparison_results = {}
        
        for category in self.target_vocabularies:
            self.logger.info(f"クラス比較: {category}")
            
            # Before/After別のクラス間比較
            before_by_class = []
            after_by_class = []
            class_labels = []
            
            for class_id in self.classes:
                before_class = before_features[
                    before_features['class'] == class_id
                ][category].astype(int)
                after_class = after_features[
                    after_features['class'] == class_id  
                ][category].astype(int)
                
                if len(before_class) > 0 and len(after_class) > 0:
                    before_by_class.append(before_class)
                    after_by_class.append(after_class)
                    class_labels.append(f'class_{class_id}')
            
            # Kruskal-Wallis検定（多群比較）
            if len(before_by_class) >= 2:
                try:
                    # Before データの検定
                    before_kw_stat, before_kw_p = stats.kruskal(*before_by_class)
                except ValueError as e:
                    if "All numbers are identical" in str(e):
                        self.logger.warning(f"Before {category}: 全値が同一のためKruskal-Wallis検定をスキップ")
                        before_kw_stat, before_kw_p = float('nan'), float('nan')
                    else:
                        raise e
                
                try:
                    # After データの検定
                    after_kw_stat, after_kw_p = stats.kruskal(*after_by_class)
                except ValueError as e:
                    if "All numbers are identical" in str(e):
                        self.logger.warning(f"After {category}: 全値が同一のためKruskal-Wallis検定をスキップ")
                        after_kw_stat, after_kw_p = float('nan'), float('nan')
                    else:
                        raise e
                
                comparison_results[category] = {
                    'before_kruskal_wallis': {
                        'statistic': float(before_kw_stat),
                        'p_value': float(before_kw_p)
                    },
                    'after_kruskal_wallis': {
                        'statistic': float(after_kw_stat),
                        'p_value': float(after_kw_p)
                    },
                    'class_labels': class_labels,
                    'class_effect_sizes': self._calculate_class_effect_sizes(
                        before_by_class, after_by_class, class_labels
                    )
                }
        
        return comparison_results
    
    def _calculate_class_effect_sizes(self, before_by_class, after_by_class, class_labels):
        """クラス別効果量計算"""
        class_effects = {}
        
        for i, class_label in enumerate(class_labels):
            before_data = before_by_class[i]
            after_data = after_by_class[i]
            
            effect_size = self._calculate_cohens_d(
                after_data.mean(), before_data.mean(),
                after_data.std(), before_data.std(),
                len(after_data), len(before_data)
            )
            
            class_effects[class_label] = {
                'effect_size': float(effect_size),
                'before_mean': float(before_data.mean()),
                'after_mean': float(after_data.mean()),
                'change_rate': float((after_data.mean() - before_data.mean()) / before_data.mean() * 100) if before_data.mean() > 0 else 0
            }
        
        return class_effects
    
    def visualize_results(self, usage_rates, test_results, comparison_results):
        """結果可視化"""
        self.logger.info("可視化開始")
        
        # 図のスタイル設定
        plt.style.use('seaborn-v0_8')
        
        # 1. 語彙使用率変化のヒートマップ
        self._plot_usage_change_heatmap(usage_rates)
        
        # 2. クラス別効果量比較
        self._plot_class_effect_sizes(comparison_results)
        
        # 3. 統計的検定結果の森林プロット
        self._plot_forest_plot(test_results)
        
        self.logger.info("可視化完了")
    
    def _plot_usage_change_heatmap(self, usage_rates):
        """語彙使用率変化ヒートマップ"""
        # データ準備
        before_rates = usage_rates['before']['overall']
        after_rates = usage_rates['after']['overall']
        
        # 変化率計算
        change_data = []
        categories = list(self.target_vocabularies.keys())
        
        for category in categories:
            before_rate = before_rates.get(category, 0)
            after_rate = after_rates.get(category, 0)
            change_rate = ((after_rate - before_rate) / before_rate * 100) if before_rate > 0 else 0
            change_data.append([before_rate * 100, after_rate * 100, change_rate])
        
        # ヒートマップ作成
        fig, ax = plt.subplots(figsize=(10, 6))
        
        data_array = np.array(change_data)
        im = ax.imshow(data_array, cmap='RdYlBu_r', aspect='auto')
        
        # ラベル設定
        ax.set_xticks(range(3))
        ax.set_xticklabels(['Before (%)', 'After (%)', 'Change (%)'])
        ax.set_yticks(range(len(categories)))
        ax.set_yticklabels(categories)
        
        # 数値表示
        for i in range(len(categories)):
            for j in range(3):
                ax.text(j, i, f'{data_array[i, j]:.1f}', 
                       ha='center', va='center', color='black')
        
        plt.title('語彙使用率変化ヒートマップ')
        plt.colorbar(im)
        plt.tight_layout()
        plt.savefig('outputs/vocabulary/usage_change_heatmap.png', dpi=300)
        plt.close()
    
    def _plot_class_effect_sizes(self, comparison_results):
        """クラス別効果量比較プロット"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for i, category in enumerate(self.target_vocabularies.keys()):
            if category not in comparison_results:
                continue
                
            class_effects = comparison_results[category]['class_effect_sizes']
            
            classes = list(class_effects.keys())
            effect_sizes = [class_effects[cls]['effect_size'] for cls in classes]
            
            # 効果量プロット
            bars = axes[i].bar(classes, effect_sizes, 
                              color=['red' if es < 0 else 'blue' for es in effect_sizes])
            
            # 効果量の意味的閾値
            axes[i].axhline(y=0.2, color='green', linestyle='--', label='小効果')
            axes[i].axhline(y=0.5, color='orange', linestyle='--', label='中効果')
            axes[i].axhline(y=0.8, color='red', linestyle='--', label='大効果')
            
            axes[i].set_title(f'{category} - クラス別効果量')
            axes[i].set_ylabel("Cohen's d")
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('outputs/vocabulary/class_effect_sizes.png', dpi=300)
        plt.close()
    
    def _plot_forest_plot(self, test_results):
        """統計検定結果の森林プロット"""
        categories = list(test_results.keys())
        effect_sizes = [test_results[cat]['effect_size_cohens_d'] for cat in categories]
        ci_lower = [test_results[cat]['confidence_interval'][0] for cat in categories]
        ci_upper = [test_results[cat]['confidence_interval'][1] for cat in categories]
        p_values = [test_results[cat]['p_value'] for cat in categories]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        y_pos = np.arange(len(categories))
        
        # 効果量プロット
        colors = ['red' if p > 0.05 else 'blue' for p in p_values]
        ax.scatter(effect_sizes, y_pos, color=colors, s=100)
        
        # 信頼区間
        for i in range(len(categories)):
            ax.plot([ci_lower[i], ci_upper[i]], [i, i], color=colors[i], linewidth=2)
        
        # 効果なしライン
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.5)
        
        # 効果量閾値
        ax.axvline(x=0.2, color='green', linestyle='--', alpha=0.7, label='小効果')
        ax.axvline(x=0.5, color='orange', linestyle='--', alpha=0.7, label='中効果')
        ax.axvline(x=0.8, color='red', linestyle='--', alpha=0.7, label='大効果')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories)
        ax.set_xlabel("Cohen's d (95% CI)")
        ax.set_title('語彙カテゴリ別効果量・信頼区間')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('outputs/vocabulary/forest_plot.png', dpi=300)
        plt.close()
    
    def save_results(self, usage_rates, test_results, comparison_results):
        """結果保存"""
        self.logger.info("結果保存開始")
        
        # 出力ディレクトリ作成
        Path('outputs/vocabulary').mkdir(parents=True, exist_ok=True)
        
        # 使用率データ保存
        with open('outputs/vocabulary/usage_rates.json', 'w', encoding='utf-8') as f:
            json.dump(usage_rates, f, ensure_ascii=False, indent=2)
        
        # 統計検定結果保存
        with open('outputs/vocabulary/statistical_results.json', 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        # クラス比較結果保存
        with open('outputs/vocabulary/class_comparison_results.json', 'w', encoding='utf-8') as f:
            json.dump(comparison_results, f, ensure_ascii=False, indent=2)
        
        # CSV形式での要約保存
        self._save_summary_csv(test_results)
        
        self.logger.info("結果保存完了")
    
    def _save_summary_csv(self, test_results):
        """要約結果をCSV保存"""
        summary_data = []
        
        for category, results in test_results.items():
            summary_data.append({
                'vocabulary_category': category,
                'before_usage_rate': results['before_mean'],
                'after_usage_rate': results['after_mean'], 
                'effect_size_cohens_d': results['effect_size_cohens_d'],
                'p_value': results['p_value'],
                'significant': results['p_value'] < 0.05,
                'meaningful_effect': abs(results['effect_size_cohens_d']) > 0.2,
                'ci_lower': results['confidence_interval'][0],
                'ci_upper': results['confidence_interval'][1]
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv('outputs/vocabulary/results_summary.csv', 
                         index=False, encoding='utf-8')
    
    def run_analysis(self):
        """メイン分析実行"""
        self.logger.info("語彙変化分析開始")
        
        try:
            # 1. データ読み込み
            self.load_data()
            
            # 2. 語彙使用率計算
            before_rates, before_features = self.calculate_usage_rates(self.before_data)
            after_rates, after_features = self.calculate_usage_rates(self.after_data)
            
            usage_rates = {
                'before': before_rates,
                'after': after_rates
            }
            
            # 3. 統計的検定
            test_results = self.statistical_testing(before_features, after_features)
            
            # 4. クラス間比較
            comparison_results = self.class_comparison_analysis(before_features, after_features)
            
            # 5. 可視化
            self.visualize_results(usage_rates, test_results, comparison_results)
            
            # 6. 結果保存
            self.save_results(usage_rates, test_results, comparison_results)
            
            # 7. 主要結果の要約表示
            self._print_summary(test_results)
            
            self.logger.info("語彙変化分析完了")
            
        except Exception as e:
            self.logger.error(f"分析エラー: {e}")
            raise
    
    def _print_summary(self, test_results):
        """主要結果要約表示"""
        print("\n" + "="*60)
        print("語彙変化分析結果要約")
        print("="*60)
        
        for category, results in test_results.items():
            print(f"\n【{category}】")
            print(f"  Before使用率: {results['before_mean']:.3f}")
            print(f"  After使用率:  {results['after_mean']:.3f}")
            print(f"  効果量(d):    {results['effect_size_cohens_d']:.3f}")
            print(f"  p値:         {results['p_value']:.4f}")
            print(f"  有意差:       {'あり' if results['p_value'] < 0.05 else 'なし'}")
            print(f"  実質的効果:   {'あり' if abs(results['effect_size_cohens_d']) > 0.2 else 'なし'}")


if __name__ == "__main__":
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    Path('outputs/vocabulary').mkdir(parents=True, exist_ok=True)
    
    # 分析実行
    analyzer = VocabularyAnalyzer()
    analyzer.run_analysis()