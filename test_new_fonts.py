#!/usr/bin/env python3
"""
新しいフォントのテスト
Noto Sans JPとNoto Serif JPでワードクラウドを生成
"""

from wordcloud import WordCloud
import matplotlib.pyplot as plt
from pathlib import Path

# プロジェクトルート
project_root = Path(__file__).parent

# テストテキスト（教育効果を示すキーワード）
test_text = """
東京工業大学 出前授業 科学教育 ナトリウム 塩化ナトリウム
炎色反応 実験 観察 小学生 理科教育 教育効果
塩 みそ汁 食塩 化学 サイエンス 学習
興味 関心 楽しい 面白い わかりやすい
"""

# 新しいフォントのテスト
fonts_to_test = [
    ("Noto Sans JP", "fonts/NotoSansJP-Regular.otf"),
    ("Noto Serif JP", "fonts/NotoSerifJP-Regular.otf"),
    ("はんなり明朝（代替）", "fonts/ipaexm.ttf"),  # IPAex明朝で代替
]

output_dir = Path("outputs/font_tests")
output_dir.mkdir(parents=True, exist_ok=True)

for font_name, font_path in fonts_to_test:
    try:
        print(f"テスト中: {font_name}")
        
        # ワードクラウド生成
        wordcloud = WordCloud(
            font_path=str(project_root / font_path),
            width=600,
            height=300,
            background_color='white',
            max_words=30,
            colormap='viridis'
        ).generate(test_text)
        
        # 画像保存
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'{font_name} - ワードクラウドテスト', fontsize=14, pad=10)
        plt.tight_layout()
        
        output_file = output_dir / f'new_font_test_{font_name.replace(" ", "_")}.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ {font_name} テスト成功: {output_file}")
        
    except Exception as e:
        print(f"❌ {font_name} テスト失敗: {e}")

print(f"\n📁 テスト結果保存先: {output_dir}")
print("🎉 新しいフォントのテスト完了！")
print("\n💡 Webアプリケーションを起動して、ブラウザで http://localhost:5000 にアクセスすると、")
print("   これらの新しいフォントがドロップダウンリストに表示されます。")