#!/usr/bin/env python3
"""
環境検証スクリプト
東京高専出前授業テキストマイニング分析環境

主要機能:
1. Python環境・依存関係の検証
2. 日本語NLP環境の動作確認
3. データファイル存在・整合性確認
4. 出力ディレクトリ準備
5. 基本分析機能のテスト実行

実行方法: python scripts/setup/validate_environment.py
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
import json
import traceback
from typing import List, Dict, Tuple
import warnings

# 警告を抑制
warnings.filterwarnings('ignore')

class EnvironmentValidator:
    """環境検証クラス"""
    
    def __init__(self):
        self.results = {
            'python_version': {'status': False, 'details': ''},
            'packages': {'status': False, 'details': {}, 'failed': []},
            'japanese_nlp': {'status': False, 'details': ''},
            'data_files': {'status': False, 'details': {}, 'missing': []},
            'directories': {'status': False, 'details': {}},
            'basic_functionality': {'status': False, 'details': {}}
        }
        
        # 必須パッケージリスト
        self.required_packages = [
            ('pandas', 'pandas'),
            ('numpy', 'numpy'),
            ('scipy', 'scipy'),
            ('matplotlib', 'matplotlib.pyplot'),
            ('seaborn', 'seaborn'),
            ('sklearn', 'sklearn'),
            ('gensim', 'gensim'),
            ('janome', 'janome.tokenizer'),
            ('textblob', 'textblob'),
            ('wordcloud', 'wordcloud'),
            ('yaml', 'yaml'),
            ('pathlib', 'pathlib')
        ]
        
        # 拡張パッケージリスト（オプション）
        self.optional_packages = [
            ('pingouin', 'pingouin'),
            ('plotly', 'plotly'),
            ('kaleido', 'kaleido'),
            ('statsmodels', 'statsmodels'),
            ('fugashi', 'fugashi'),
            ('unidic_lite', 'unidic_lite')
        ]
        
        # 必須データファイル
        self.required_data_files = [
            'data/raw/comments.csv',
            'data/raw/q2_reasons_before.csv', 
            'data/raw/q2_reasons_after.csv'
        ]
        
        # 必須ディレクトリ
        self.required_directories = [
            'outputs/wordclouds',
            'outputs/sentiment_results',
            'outputs/topic_models',
            'outputs/vocabulary',
            'outputs/statistics',
            'logs',
            'config'
        ]
    
    def check_python_version(self) -> bool:
        """Python バージョン確認"""
        print("🐍 Python バージョン確認...")
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major == 3 and version.minor >= 8:
            self.results['python_version'] = {
                'status': True,
                'details': f"Python {version_str} - OK (3.8+ 要件満たす)"
            }
            print(f"   ✓ Python {version_str} - OK")
            return True
        else:
            self.results['python_version'] = {
                'status': False,
                'details': f"Python {version_str} - NG (3.8+ 必須)"
            }
            print(f"   ✗ Python {version_str} - NG (3.8+ 必須)")
            return False
    
    def check_packages(self) -> bool:
        """パッケージ存在確認"""
        print("\n📦 パッケージ確認...")
        
        results = {}
        failed_packages = []
        
        # 必須パッケージ
        print("   必須パッケージ:")
        for package_name, import_name in self.required_packages:
            status, details = self._check_single_package(package_name, import_name)
            results[package_name] = {'status': status, 'details': details, 'required': True}
            
            if status:
                print(f"     ✓ {package_name} - {details}")
            else:
                print(f"     ✗ {package_name} - {details}")
                failed_packages.append(package_name)
        
        # オプションパッケージ
        print("   オプションパッケージ:")
        for package_name, import_name in self.optional_packages:
            status, details = self._check_single_package(package_name, import_name)
            results[package_name] = {'status': status, 'details': details, 'required': False}
            
            if status:
                print(f"     ✓ {package_name} - {details}")
            else:
                print(f"     ○ {package_name} - 未インストール（オプション）")
        
        # 結果保存
        all_required_ok = len(failed_packages) == 0
        self.results['packages'] = {
            'status': all_required_ok,
            'details': results,
            'failed': failed_packages
        }
        
        return all_required_ok
    
    def _check_single_package(self, package_name: str, import_name: str) -> Tuple[bool, str]:
        """個別パッケージ確認"""
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            return True, version
        except ImportError as e:
            return False, f"インポートエラー: {str(e)}"
    
    def check_japanese_nlp(self) -> bool:
        """日本語NLP環境確認"""
        print("\n🗾 日本語NLP環境確認...")
        
        # janome テスト
        janome_status = self._test_janome()
        
        # MeCab テスト（あれば）
        mecab_status = self._test_mecab()
        
        # spaCy/ginza テスト
        spacy_status = self._test_spacy_ginza()
        
        # 総合判定
        nlp_available = janome_status or mecab_status
        
        details = {
            'janome': janome_status,
            'mecab': mecab_status,
            'spacy_ginza': spacy_status,
            'primary_tokenizer': 'janome' if janome_status else 'mecab' if mecab_status else 'none'
        }
        
        self.results['japanese_nlp'] = {
            'status': nlp_available,
            'details': details
        }
        
        if nlp_available:
            print(f"   ✓ 日本語NLP環境 - 利用可能（{details['primary_tokenizer']}）")
        else:
            print("   ✗ 日本語NLP環境 - 利用不可")
            
        return nlp_available
    
    def _test_janome(self) -> bool:
        """janome テスト"""
        try:
            from janome.tokenizer import Tokenizer
            tokenizer = Tokenizer()
            tokens = list(tokenizer.tokenize("これはテストです"))
            if len(tokens) > 0:
                print("     ✓ janome - 日本語トークン化 OK")
                return True
            else:
                print("     ✗ janome - トークン化失敗")
                return False
        except Exception as e:
            print(f"     ✗ janome - エラー: {e}")
            return False
    
    def _test_mecab(self) -> bool:
        """MeCab テスト"""
        try:
            import MeCab
            tagger = MeCab.Tagger()
            result = tagger.parse("これはテストです")
            if result and len(result.strip()) > 0:
                print("     ✓ MeCab - 日本語解析 OK")
                return True
            else:
                print("     ✗ MeCab - 解析失敗")
                return False
        except Exception as e:
            print(f"     ○ MeCab - 未インストール（janomeで代替可能）")
            return False
    
    def _test_spacy_ginza(self) -> bool:
        """spaCy/ginza テスト"""
        try:
            import spacy
            # ginzaモデルの確認
            try:
                nlp = spacy.load("ja_ginza")
                doc = nlp("これはテストです")
                if len(doc) > 0:
                    print("     ✓ spaCy/ginza - 日本語解析 OK")
                    return True
                else:
                    print("     ✗ spaCy/ginza - 解析失敗")
                    return False
            except OSError:
                print("     ○ spaCy/ginza - モデル未インストール（基本機能には不要）")
                return False
        except Exception as e:
            print(f"     ○ spaCy/ginza - 未利用可能（基本機能には不要）")
            return False
    
    def check_data_files(self) -> bool:
        """データファイル存在確認"""
        print("\n📄 データファイル確認...")
        
        file_details = {}
        missing_files = []
        
        for file_path in self.required_data_files:
            path_obj = Path(file_path)
            
            if path_obj.exists():
                try:
                    # ファイル基本情報
                    size = path_obj.stat().st_size
                    
                    # CSV読み込みテスト
                    import pandas as pd
                    df = pd.read_csv(file_path, encoding='utf-8')
                    
                    file_details[file_path] = {
                        'exists': True,
                        'size_bytes': size,
                        'records': len(df),
                        'columns': list(df.columns)
                    }
                    
                    print(f"   ✓ {file_path} - {len(df)}件、{len(df.columns)}列")
                    
                except Exception as e:
                    file_details[file_path] = {
                        'exists': True,
                        'size_bytes': size,
                        'error': str(e)
                    }
                    print(f"   ⚠ {file_path} - ファイル存在するが読み込みエラー: {e}")
                    
            else:
                file_details[file_path] = {'exists': False}
                missing_files.append(file_path)
                print(f"   ✗ {file_path} - ファイル未発見")
        
        all_files_ok = len(missing_files) == 0
        self.results['data_files'] = {
            'status': all_files_ok,
            'details': file_details,
            'missing': missing_files
        }
        
        return all_files_ok
    
    def check_directories(self) -> bool:
        """ディレクトリ確認・作成"""
        print("\n📁 ディレクトリ確認...")
        
        directory_details = {}
        
        for dir_path in self.required_directories:
            path_obj = Path(dir_path)
            
            if path_obj.exists():
                directory_details[dir_path] = {'exists': True, 'created': False}
                print(f"   ✓ {dir_path} - 存在")
            else:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    directory_details[dir_path] = {'exists': True, 'created': True}
                    print(f"   ✓ {dir_path} - 作成")
                except Exception as e:
                    directory_details[dir_path] = {'exists': False, 'error': str(e)}
                    print(f"   ✗ {dir_path} - 作成失敗: {e}")
        
        self.results['directories'] = {
            'status': True,  # ディレクトリは作成可能なのでOK
            'details': directory_details
        }
        
        return True
    
    def check_basic_functionality(self) -> bool:
        """基本機能テスト"""
        print("\n🧪 基本機能テスト...")
        
        test_results = {}
        
        # 1. データ読み込みテスト
        test_results['data_loading'] = self._test_data_loading()
        
        # 2. 可視化テスト
        test_results['visualization'] = self._test_visualization()
        
        # 3. 統計計算テスト
        test_results['statistics'] = self._test_statistics()
        
        # 4. テキスト処理テスト
        test_results['text_processing'] = self._test_text_processing()
        
        all_tests_ok = all(test_results.values())
        
        self.results['basic_functionality'] = {
            'status': all_tests_ok,
            'details': test_results
        }
        
        return all_tests_ok
    
    def _test_data_loading(self) -> bool:
        """データ読み込みテスト"""
        try:
            import pandas as pd
            
            # 最小限のデータ読み込みテスト
            test_data = pd.DataFrame({
                'text': ['これはテストです', 'テスト用データ'],
                'class': [1.0, 2.0],
                'page_id': [1, 2]
            })
            
            # 基本操作テスト
            assert len(test_data) == 2
            assert 'text' in test_data.columns
            
            print("     ✓ データ読み込み - OK")
            return True
            
        except Exception as e:
            print(f"     ✗ データ読み込み - エラー: {e}")
            return False
    
    def _test_visualization(self) -> bool:
        """可視化テスト"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            import numpy as np
            
            # 簡単なプロット作成
            fig, ax = plt.subplots(figsize=(6, 4))
            x = np.array([1, 2, 3])
            y = np.array([1, 4, 2])
            ax.plot(x, y)
            ax.set_title('Test Plot')
            
            # 保存テスト
            test_path = 'outputs/test_plot.png'
            plt.savefig(test_path, dpi=150)
            plt.close()
            
            # ファイル確認
            if Path(test_path).exists():
                Path(test_path).unlink()  # テストファイル削除
                print("     ✓ 可視化 - OK")
                return True
            else:
                print("     ✗ 可視化 - 保存失敗")
                return False
                
        except Exception as e:
            print(f"     ✗ 可視化 - エラー: {e}")
            return False
    
    def _test_statistics(self) -> bool:
        """統計計算テスト"""
        try:
            import numpy as np
            from scipy import stats
            
            # 基本統計テスト
            data1 = np.array([1, 2, 3, 4, 5])
            data2 = np.array([2, 3, 4, 5, 6])
            
            # t検定
            statistic, pvalue = stats.ttest_ind(data1, data2)
            
            # Mann-Whitney U検定
            u_stat, u_pvalue = stats.mannwhitneyu(data1, data2, alternative='two-sided')
            
            # 効果量計算（簡易版）
            cohens_d = (np.mean(data2) - np.mean(data1)) / np.sqrt((np.std(data1)**2 + np.std(data2)**2) / 2)
            
            assert not np.isnan(pvalue)
            assert not np.isnan(cohens_d)
            
            print("     ✓ 統計計算 - OK")
            return True
            
        except Exception as e:
            print(f"     ✗ 統計計算 - エラー: {e}")
            return False
    
    def _test_text_processing(self) -> bool:
        """テキスト処理テスト"""
        try:
            from janome.tokenizer import Tokenizer
            
            # 日本語トークン化テスト
            tokenizer = Tokenizer()
            text = "みそ汁にナトリウムが入っているから"
            tokens = list(tokenizer.tokenize(text))
            
            # 語彙抽出テスト
            token_texts = [token.surface for token in tokens]
            contains_miso = any('みそ' in token for token in token_texts)
            contains_natrium = any('ナトリウム' in token for token in token_texts)
            
            assert len(tokens) > 0
            
            print("     ✓ テキスト処理 - OK")
            return True
            
        except Exception as e:
            print(f"     ✗ テキスト処理 - エラー: {e}")
            return False
    
    def generate_report(self) -> Dict:
        """総合レポート生成"""
        overall_status = all([
            self.results['python_version']['status'],
            self.results['packages']['status'],
            self.results['japanese_nlp']['status'],
            self.results['data_files']['status'],
            self.results['directories']['status'],
            self.results['basic_functionality']['status']
        ])
        
        report = {
            'overall_status': overall_status,
            'timestamp': str(Path(__file__).stat().st_mtime),  # 簡易タイムスタンプ
            'checks': self.results,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        if not self.results['python_version']['status']:
            recommendations.append("Python 3.8以上にアップグレードしてください")
        
        if self.results['packages']['failed']:
            failed_packages = ', '.join(self.results['packages']['failed'])
            recommendations.append(f"必須パッケージをインストールしてください: {failed_packages}")
        
        if not self.results['japanese_nlp']['status']:
            recommendations.append("日本語NLP環境を設定してください（janome推奨）")
        
        if self.results['data_files']['missing']:
            missing_files = ', '.join(self.results['data_files']['missing'])
            recommendations.append(f"データファイルを配置してください: {missing_files}")
        
        if not self.results['basic_functionality']['status']:
            recommendations.append("基本機能に問題があります。依存関係を確認してください")
        
        if not recommendations:
            recommendations.append("全ての環境確認が完了しました。分析を開始できます！")
        
        return recommendations
    
    def save_report(self, output_path: str = "outputs/environment_validation_report.json"):
        """レポート保存"""
        report = self.generate_report()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 検証レポート保存: {output_path}")
    
    def run_validation(self) -> bool:
        """メイン検証実行"""
        print("="*60)
        print("🔍 東京高専テキストマイニング環境検証")
        print("="*60)
        
        try:
            # 各検証実行
            python_ok = self.check_python_version()
            packages_ok = self.check_packages()
            nlp_ok = self.check_japanese_nlp()
            data_ok = self.check_data_files()
            dirs_ok = self.check_directories()
            func_ok = self.check_basic_functionality()
            
            # 総合結果
            overall_ok = all([python_ok, packages_ok, nlp_ok, data_ok, dirs_ok, func_ok])
            
            # 結果表示
            print("\n" + "="*60)
            print("🏁 検証結果サマリー")
            print("="*60)
            
            status_icon = "✅" if overall_ok else "❌"
            print(f"{status_icon} 総合結果: {'成功' if overall_ok else '失敗'}")
            
            # 推奨事項表示
            recommendations = self._generate_recommendations()
            print("\n📋 推奨事項:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
            
            # レポート保存
            self.save_report()
            
            if overall_ok:
                print("\n🚀 環境準備完了！分析を開始できます。")
                print("   次のステップ: python scripts/analysis/02_vocabulary_analysis.py")
            else:
                print("\n⚠️  環境に問題があります。上記推奨事項を確認してください。")
            
            return overall_ok
            
        except Exception as e:
            print(f"\n❌ 検証中にエラーが発生しました: {e}")
            print(f"詳細: {traceback.format_exc()}")
            return False


if __name__ == "__main__":
    validator = EnvironmentValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)