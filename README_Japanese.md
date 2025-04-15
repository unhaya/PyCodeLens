# 🔍 PyCodeLens: LLM向けPythonコード分析ツール

[![GitHub Stars](https://img.shields.io/github/stars/unhaya/pycodelens?style=social)](https://github.com/unhaya/pycodelens)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)

> **LLMが複雑なコードベースに直面したとき、PyCodeLensがその目となります。**

PyCodeLensは、開発者が大規模言語モデル（LLM）と複雑なコードベースで作業するために特別に設計された強力なPythonコード分析ツールです。何千行ものコードでLLMを圧倒するのではなく、代わりに構造化された洞察を提供しましょう。

## 🌟 なぜPyCodeLensなのか？

ClaudeやGPTに大規模なコードベースを理解させようとしたことはありますか？大変ですよね？

**問題点:** LLMにはトークン制限があり、大規模な複数ファイルのコードベースの処理に苦労します
**解決策:** PyCodeLensはLLMが必要とする重要な構造情報を抽出します

## 🚀 主な機能

- 🔄 **スマートなコードベース要約**: 複雑なPythonコードベースをLLMフレンドリーなJSONに変換
- 🧩 **クラス＆メソッド分析**: すべてのクラス、メソッド、およびそれらの関係を抽出
- 📊 **依存関係マッピング**: コールグラフとモジュールの依存関係を視覚化
- 🌲 **ディレクトリ構造**: クリーンで操作可能なファイルツリーを提供
- 🖥️ **UIインターフェース**: 分析を探索・エクスポートするための直感的なGUI
- 📋 **クリップボード統合**: 結果を直接コピーしてLLMですぐに使用可能
- 🔌 **拡張可能なアーキテクチャ**: より多くの言語や分析タイプの追加に対応

## 💡 こんな方におすすめ

- **LLM開発者**: Claude、GPTなどに構造化されたコードの洞察を提供
- **オープンソース貢献者**: 新しいプロジェクトを素早く理解
- **コードレビュアー**: プロジェクト構造の高レベルビューを取得
- **Pythonの学習者**: 実世界のPythonプロジェクトの仕組みを視覚化

## 🛠️ インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/unhaya/pycodelens.git

# プロジェクトディレクトリに移動
cd pycodelens

# 依存関係をインストール
pip install -r requirements.txt

# アプリケーションを実行
python "main.py"
```

## 📋 クイック使用ガイド

1. PyCodeLensを起動
2. Pythonファイルまたはディレクトリをインポート
3. 構造化されたタブで分析結果を表示
4. JSON出力をクリップボードにコピー
5. お好みのLLMに直接貼り付けてコーディングの質問をする

## 🔮 仕組み

PyCodeLensは複数の分析戦略を使用します：

1. **AST分析**: Pythonコードの高速な構文解析
2. **Astroid分析**: 型推論を伴う深い意味分析
3. **コールグラフ生成**: モジュール間の関数呼び出しをマッピング
4. **依存関係検出**: モジュール間の関係を識別

結果はクリーンで構造化されたJSON形式に整理され、以下のような特徴があります：
- すべての重要な関係を維持
- 不要な詳細を削除
- LLMのトークン効率を最適化

## 🖼️ スクリーンショット
<img src="screenshot/pycodelens_screenshot.png" alt="スクリーンショット" width="600" />

## 🏗️ プロジェクト構造

```
pycodelens/
├── screenshot/
│   └── pycodelens_screenshot.png
├── LICENSE.txt
├── README.md
├── README_Japanese.md
├── main.py
├── requirements.txt
└── simple_json_converter.py
```

### 主要コンポーネント

- **ConfigManager**: アプリケーション設定と以前のセッションを処理
- **CodeAnalyzer**: コード分析のための基本クラス
- **AstroidAnalyzer**: Astroidによる深い意味分析
- **DirectoryTreeView**: プロジェクトファイルをナビゲートするためのUI
- **SyntaxHighlighter**: コード視覚化ヘルパー
- **CodeAnalyzerApp**: メインアプリケーションUI

## 🚀 ロードマップ

- [ ] 追加のプログラミング言語のサポート（JavaScript、Java、C++）
- [ ] 複数形式でのエクスポート（PDF、HTML、Markdown）
- [ ] LLM API統合のためのプラグイン
- [ ] ブラウザベースの分析のためのWebバージョン
- [ ] 非常に大規模なコードベースのためのパフォーマンス最適化
- [ ] 完全なテストカバレッジとCI/CDパイプライン

## 👥 貢献

貢献は、オープンソースコミュニティをそのような素晴らしい学習、インスピレーション、創造の場にするものです。あなたの貢献は**大いに感謝されます**。

貢献方法：

1. プロジェクトをフォーク
2. 機能ブランチを作成（`git checkout -b feature/AmazingFeature`）
3. 変更をコミット（`git commit -m 'Add some AmazingFeature'`）
4. ブランチにプッシュ（`git push origin feature/AmazingFeature`）
5. プルリクエストを開く

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)ファイルを参照してください。

## 📜 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE.txt](LICENSE.txt)ファイルを参照してください。

## 💌 連絡先

[@haasiy](https://x.com/haassiy) - haasiy@gmail.com

[https://github.com/unhaya/pycodelens/](https://github.com/unhaya/pycodelens/)

---

<p align="center">
  <b>LLM開発コミュニティのために❤️を込めて作成</b><br>
  <i>あなたのLLMにコード理解の恩恵を</i>
</p>
