#!/usr/bin/env python3
"""
データローダーユーティリティ
東京高専出前授業テキストマイニング分析プロジェクト

主要機能:
1. 統一的なデータ読み込み・検証
2. クラス情報の正規化・検証
3. データ品質レポート生成
4. 欠損値・異常値処理

使用例:
    from scripts.utils.data_loader import DataLoader
    loader = DataLoader()
    data = loader.load_all_data()
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import yaml
import json
from typing import Dict, List, Tuple, Optional
import warnings

class DataLoader:
    """統一データローダークラス"""
    
    def __init__(self, config_path: str = "config/analysis_config.yaml"):
        """初期化
        
        Args:
            config_path: 設定ファイルパス
        """
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.data_quality_report = {}
        
    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_config(self, config_path: str) -> dict:
        """設定ファイル読み込み"""
        try:
            if Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                self.logger.warning(f"設定ファイルが見つかりません: {config_path}")
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """デフォルト設定"""
        return {
            'data': {
                'encoding': 'utf-8',
                'na_values': ['', 'なし', '？', 'わからない'],
                'paths': {
                    'comments': 'data/raw/comments.csv',
                    'q2_before': 'data/raw/q2_reasons_before.csv',
                    'q2_after': 'data/raw/q2_reasons_after.csv'
                }
            },
            'class_analysis': {
                'classes': [1.0, 2.0, 3.0, 4.0],
                'min_sample_size': 3
            }
        }
    
    def load_comments_data(self) -> pd.DataFrame:
        """感想コメントデータ読み込み"""
        self.logger.info("感想コメントデータ読み込み開始")
        
        file_path = self.config['data']['paths']['comments']
        
        try:
            df = pd.read_csv(
                file_path,
                encoding=self.config['data']['encoding'],
                na_values=self.config['data']['na_values']
            )
            
            # カラム名の正規化
            df = self._normalize_comments_columns(df)
            
            # データ検証
            self._validate_comments_data(df)
            
            self.logger.info(f"感想データ読み込み完了: {len(df)}件")
            return df
            
        except Exception as e:
            self.logger.error(f"感想データ読み込みエラー: {e}")
            raise
    
    def load_q2_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Q2理由説明データ読み込み（Before/After）"""
        self.logger.info("Q2理由説明データ読み込み開始")
        
        before_path = self.config['data']['paths']['q2_before']
        after_path = self.config['data']['paths']['q2_after']
        
        try:
            # Before データ
            before_df = pd.read_csv(
                before_path,
                encoding=self.config['data']['encoding'],
                na_values=self.config['data']['na_values']
            )
            
            # After データ
            after_df = pd.read_csv(
                after_path,
                encoding=self.config['data']['encoding'],
                na_values=self.config['data']['na_values']
            )
            
            # カラム名の正規化
            before_df = self._normalize_q2_columns(before_df)
            after_df = self._normalize_q2_columns(after_df)
            
            # データ検証
            self._validate_q2_data(before_df, "before")
            self._validate_q2_data(after_df, "after")
            
            self.logger.info(f"Q2データ読み込み完了: Before {len(before_df)}件, After {len(after_df)}件")
            return before_df, after_df
            
        except Exception as e:
            self.logger.error(f"Q2データ読み込みエラー: {e}")
            raise
    
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """全データの統一読み込み"""
        self.logger.info("全データ読み込み開始")
        
        data = {}
        
        try:
            # 感想データ
            data['comments'] = self.load_comments_data()
            
            # Q2データ
            data['q2_before'], data['q2_after'] = self.load_q2_data()
            
            # 統合データ作成
            data['integrated'] = self._create_integrated_dataset(data)
            
            # データ品質レポート生成
            self.data_quality_report = self._generate_quality_report(data)
            
            self.logger.info("全データ読み込み完了")
            return data
            
        except Exception as e:
            self.logger.error(f"全データ読み込みエラー: {e}")
            raise
    
    def _normalize_comments_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """感想データのカラム名正規化"""
        # 期待されるカラム: class, page-ID, LR, comment
        column_mapping = {
            'page-ID': 'page_id',
            'Page-ID': 'page_id',
            'Page_ID': 'page_id',
            'LR': 'lr_position'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 必須カラムの確認
        required_columns = ['class', 'page_id', 'comment']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"感想データに必須カラムが不足: {missing_columns}")
            
        return df
    
    def _normalize_q2_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Q2データのカラム名正規化"""
        # カラム名の統一
        column_mapping = {
            'Page_ID': 'page_id',
            'page-ID': 'page_id',
            'Q2_MisoSaltyReason': 'reason_text',
            'Q2_MisoSalty_Reason': 'reason_text'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 必須カラムの確認
        required_columns = ['page_id', 'class', 'reason_text']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Q2データに必須カラムが不足: {missing_columns}")
            
        return df
    
    def _validate_comments_data(self, df: pd.DataFrame) -> None:
        """感想データの検証"""
        self.logger.info("感想データ検証開始")
        
        # 基本検証
        self._basic_data_validation(df, "comments")
        
        # 感想特有の検証
        # LR位置の確認（存在する場合）
        if 'lr_position' in df.columns:
            lr_values = df['lr_position'].dropna().unique()
            expected_lr = ['Left', 'Right']
            unexpected_lr = [v for v in lr_values if v not in expected_lr]
            if unexpected_lr:
                self.logger.warning(f"予期しないLR位置: {unexpected_lr}")
        
        # コメント長の確認
        comment_lengths = df['comment'].dropna().str.len()
        if len(comment_lengths) > 0:
            self.logger.info(f"コメント長統計: 平均{comment_lengths.mean():.1f}, 最大{comment_lengths.max()}, 最小{comment_lengths.min()}")
    
    def _validate_q2_data(self, df: pd.DataFrame, data_type: str) -> None:
        """Q2データの検証"""
        self.logger.info(f"Q2データ検証開始: {data_type}")
        
        # 基本検証
        self._basic_data_validation(df, f"q2_{data_type}")
        
        # Q2特有の検証
        # 理由テキスト長の確認
        reason_lengths = df['reason_text'].dropna().str.len()
        if len(reason_lengths) > 0:
            self.logger.info(f"{data_type}理由テキスト長統計: 平均{reason_lengths.mean():.1f}, 最大{reason_lengths.max()}, 最小{reason_lengths.min()}")
        
        # 空白・無効回答の確認
        empty_reasons = df['reason_text'].isna() | (df['reason_text'].str.strip() == '')
        if empty_reasons.any():
            self.logger.warning(f"{data_type}データに空白回答: {empty_reasons.sum()}件")
    
    def _basic_data_validation(self, df: pd.DataFrame, data_name: str) -> None:
        """基本的なデータ検証"""
        # データサイズ確認
        self.logger.info(f"{data_name}データサイズ: {df.shape}")
        
        # クラス情報確認
        if 'class' in df.columns:
            class_counts = df['class'].value_counts().sort_index()
            self.logger.info(f"{data_name}クラス分布: {class_counts.to_dict()}")
            
            # 期待されるクラス
            expected_classes = set(self.config['class_analysis']['classes'])
            actual_classes = set(df['class'].dropna())
            
            unexpected_classes = actual_classes - expected_classes
            missing_classes = expected_classes - actual_classes
            
            if unexpected_classes:
                self.logger.warning(f"予期しないクラス: {unexpected_classes}")
            if missing_classes:
                self.logger.warning(f"不足しているクラス: {missing_classes}")
        
        # 欠損値確認
        missing_counts = df.isnull().sum()
        if missing_counts.any():
            self.logger.info(f"{data_name}欠損値: {missing_counts[missing_counts > 0].to_dict()}")
        
        # 重複確認
        if 'page_id' in df.columns:
            duplicates = df.duplicated(subset=['page_id', 'class'])
            if duplicates.any():
                self.logger.warning(f"{data_name}重複レコード: {duplicates.sum()}件")
    
    def _create_integrated_dataset(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """統合データセット作成"""
        self.logger.info("統合データセット作成開始")
        
        integrated_records = []
        
        # 感想データの統合
        for _, row in data['comments'].iterrows():
            integrated_records.append({
                'text': row['comment'],
                'category': 'comment',
                'class': row['class'],
                'page_id': row['page_id'],
                'data_source': 'comments',
                'time_point': 'after'  # 感想は授業後
            })
        
        # Q2 Before データの統合
        for _, row in data['q2_before'].iterrows():
            integrated_records.append({
                'text': row['reason_text'],
                'category': 'reason_explanation',
                'class': row['class'],
                'page_id': row['page_id'],
                'data_source': 'q2_before',
                'time_point': 'before'
            })
        
        # Q2 After データの統合
        for _, row in data['q2_after'].iterrows():
            integrated_records.append({
                'text': row['reason_text'],
                'category': 'reason_explanation',
                'class': row['class'],
                'page_id': row['page_id'],
                'data_source': 'q2_after',
                'time_point': 'after'
            })
        
        integrated_df = pd.DataFrame(integrated_records)
        
        # 空テキストの除去
        integrated_df = integrated_df.dropna(subset=['text'])
        integrated_df = integrated_df[integrated_df['text'].str.strip() != '']
        
        self.logger.info(f"統合データセット作成完了: {len(integrated_df)}件")
        return integrated_df
    
    def _generate_quality_report(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """データ品質レポート生成"""
        report = {
            'generation_timestamp': pd.Timestamp.now().isoformat(),
            'datasets': {}
        }
        
        for dataset_name, df in data.items():
            if dataset_name == 'integrated':
                continue
                
            dataset_report = {
                'record_count': len(df),
                'column_count': len(df.columns),
                'missing_values': df.isnull().sum().to_dict(),
                'data_types': df.dtypes.astype(str).to_dict()
            }
            
            # テキストカラムの統計
            text_columns = []
            if 'comment' in df.columns:
                text_columns.append('comment')
            if 'reason_text' in df.columns:
                text_columns.append('reason_text')
                
            for col in text_columns:
                if col in df.columns:
                    text_series = df[col].dropna()
                    if len(text_series) > 0:
                        lengths = text_series.str.len()
                        dataset_report[f'{col}_statistics'] = {
                            'count': len(text_series),
                            'mean_length': float(lengths.mean()),
                            'std_length': float(lengths.std()),
                            'min_length': int(lengths.min()),
                            'max_length': int(lengths.max()),
                            'empty_rate': float((text_series.str.strip() == '').mean())
                        }
            
            # クラス分布
            if 'class' in df.columns:
                dataset_report['class_distribution'] = df['class'].value_counts().to_dict()
                
            report['datasets'][dataset_name] = dataset_report
        
        # 統合データの追加統計
        if 'integrated' in data:
            integrated_df = data['integrated']
            report['integrated_statistics'] = {
                'total_records': len(integrated_df),
                'by_category': integrated_df['category'].value_counts().to_dict(),
                'by_time_point': integrated_df['time_point'].value_counts().to_dict(),
                'by_class': integrated_df['class'].value_counts().to_dict(),
                'text_length_overall': {
                    'mean': float(integrated_df['text'].str.len().mean()),
                    'std': float(integrated_df['text'].str.len().std())
                }
            }
        
        return report
    
    def save_quality_report(self, output_path: str = "outputs/data_quality_report.json") -> None:
        """品質レポート保存"""
        if not self.data_quality_report:
            self.logger.warning("品質レポートが生成されていません")
            return
            
        # 出力ディレクトリ作成
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data_quality_report, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"品質レポート保存完了: {output_path}")
    
    def get_class_statistics(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """クラス別統計情報取得"""
        class_stats = {}
        
        for dataset_name, df in data.items():
            if 'class' not in df.columns:
                continue
                
            class_stats[dataset_name] = {}
            
            for class_id in self.config['class_analysis']['classes']:
                class_data = df[df['class'] == class_id]
                
                stats = {
                    'count': len(class_data),
                    'missing_rate': float(class_data.isnull().any(axis=1).mean())
                }
                
                # テキスト統計
                text_col = None
                if 'comment' in class_data.columns:
                    text_col = 'comment'
                elif 'reason_text' in class_data.columns:
                    text_col = 'reason_text'
                elif 'text' in class_data.columns:
                    text_col = 'text'
                    
                if text_col:
                    text_data = class_data[text_col].dropna()
                    if len(text_data) > 0:
                        lengths = text_data.str.len()
                        stats['text_statistics'] = {
                            'mean_length': float(lengths.mean()),
                            'std_length': float(lengths.std()),
                            'min_length': int(lengths.min()),
                            'max_length': int(lengths.max())
                        }
                
                class_stats[dataset_name][f'class_{class_id}'] = stats
        
        return class_stats
    
    def export_processed_data(self, data: Dict[str, pd.DataFrame], output_dir: str = "data/processed") -> None:
        """処理済みデータのエクスポート"""
        self.logger.info("処理済みデータエクスポート開始")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 各データセットの保存
        for dataset_name, df in data.items():
            file_path = output_path / f"{dataset_name}_processed.csv"
            df.to_csv(file_path, index=False, encoding='utf-8')
            self.logger.info(f"{dataset_name}データ保存: {file_path}")
        
        # メタデータ保存
        metadata = {
            'export_timestamp': pd.Timestamp.now().isoformat(),
            'datasets': {name: len(df) for name, df in data.items()},
            'processing_config': self.config,
            'quality_report': self.data_quality_report
        }
        
        metadata_path = output_path / "processing_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"メタデータ保存: {metadata_path}")
        self.logger.info("処理済みデータエクスポート完了")


if __name__ == "__main__":
    # テスト実行
    loader = DataLoader()
    
    try:
        # 全データ読み込み
        data = loader.load_all_data()
        
        # 品質レポート保存
        loader.save_quality_report()
        
        # クラス統計表示
        class_stats = loader.get_class_statistics(data)
        print("\nクラス別統計:")
        for dataset, stats in class_stats.items():
            print(f"\n{dataset}:")
            for class_name, class_stat in stats.items():
                print(f"  {class_name}: {class_stat['count']}件")
        
        # 処理済みデータエクスポート
        loader.export_processed_data(data)
        
        print("\nデータローダーテスト完了")
        
    except Exception as e:
        print(f"エラー: {e}")
        raise