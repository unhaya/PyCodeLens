# 🔍 PyCodeLens: LLM対応Pythonコード解析ツール

[![GitHub Stars](https://img.shields.io/github/stars/your-username/pycodelens?style=social)](https://github.com/your-username/pycodelens)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)

> **LLMが複雑なコードベースに直面したとき、PyCodeLensが彼らの目となります。**

PyCodeLensは、開発者が大規模言語モデル（LLM）と複雑なコードベースで作業するために特別に設計された強力なPythonコード分析ツールです。何千行ものコードでLLMを圧倒するのではなく、構造化された洞察を提供しましょう。

![PyCodeLens デモ](https://via.placeholder.com/800x400?text=PyCodeLens+Demo)

## 🌟 なぜPyCodeLensが必要か？

ClaudeやGPTに大規模なコードベースを理解させようとしたことはありますか？苦労しましたよね？

**問題:** LLMにはトークン制限があり、大規模な複数ファイルのコードベースの処理に苦戦します
**解決策:** PyCodeLensはLLMが必要とする重要な構造情報を抽出します

## 🚀 主な機能

- 🔄 **スマートなコードベース要約**: 複雑なPythonコードベースをLLMフレンドリーなJSONに変換
- 🧩 **クラス＆メソッド解析**: すべてのクラス、メソッド、およびそれらの関係を抽出
- 📊 **依存関係マッピング**: 関数呼び出しグラフとモジュール依存関係を可視化
- 🌲 **ディレクトリ構造**: クリーンで操作しやすいファイルツリーを提供
- 🖥️ **UIインターフェース**: 解析結果を探索・エクスポートするための直感的なGUI
- 📋 **クリップボード連携**: 結果を直接コピーしてLLMですぐに使用可能
- 🔌 **拡張可能なアーキテクチャ**: 他の言語や分析タイプを追加できる準備完了

## 💡 こんな方におすすめ

- **LLM開発者**: Claude、GPTなどに構造化されたコードの洞察を提供
- **オープンソース貢献者**: 新しいプロジェクトを迅速に理解
- **コードレビュアー**: プロジェクト構造の高レベルな概要を把握
- **Python学習者**: 実際のPythonプロジェクトがどのように機能するかを視覚化

## 🛠️ インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/your-username/pycodelens.git

# プロジェクトディレクトリに移動
cd pycodelens

# 依存関係をインストール
pip install -r requirements.txt

# アプリケーションを実行
python main.py
```

## 📋 クイック使用ガイド

1. PyCodeLensを起動
2. Pythonファイルまたはディレクトリをインポート
3. 構造化されたタブで解析結果を表示
4. JSON出力をクリップボードにコピー
5. お気に入りのLLMに直接貼り付けてコーディングの質問をする

## 🔮 仕組み

PyCodeLensは複数の解析戦略を使用します：

1. **AST解析**: Pythonコードの高速な構文解析
2. **Astroid解析**: 型推論を伴う深い意味解析
3. **コールグラフ生成**: モジュール間の関数呼び出しをマッピング
4. **依存関係検出**: モジュール関係を識別

結果はクリーンで構造化されたJSON形式にまとめられ：
- すべての重要な関係を維持
- 不要な詳細を削除
- LLMのトークン効率を最適化

## 🖼️ スクリーンショット

<div align="center">
  <img src="https://via.placeholder.com/400x250?text=ディレクトリツリー" alt="ディレクトリツリー" style="margin-right:10px"/>
  <img src="https://via.placeholder.com/400x250?text=解析結果" alt="解析結果"/>
</div>

## 🏗️ プロジェクト構造

```
code_analysis/
├── code_analysis.py       # コア解析機能
└── simple_json_converter.py  # JSON変換ユーティリティ
```

### 主要コンポーネント

- **ConfigManager**: アプリケーション設定と前回のセッションを管理
- **CodeAnalyzer**: コード解析のベースクラス
- **AstroidAnalyzer**: Astroidによる深い意味解析
- **DirectoryTreeView**: プロジェクトファイルをナビゲートするためのUI
- **SyntaxHighlighter**: コード可視化ヘルパー
- **CodeAnalyzerApp**: メインアプリケーションUI

## 🚀 ロードマップ

- [ ] 追加のプログラミング言語（JavaScript、Java、C++）のサポート
- [ ] 複数の形式（PDF、HTML、Markdown）でのエクスポート
- [ ] LLM API直接統合のためのプラグイン
- [ ] ブラウザベースの解析のためのウェブ版
- [ ] 非常に大規模なコードベースのパフォーマンス最適化
- [ ] 完全なテストカバレッジとCI/CDパイプライン

## 👥 貢献する

貢献は、オープンソースコミュニティを学習、インスピレーション、創造のための素晴らしい場所にするものです。あなたの貢献は**大いに感謝**されます。

貢献する方法：

1. プロジェクトをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを開く

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)ファイルをご覧ください。

## 📜 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)ファイルをご覧ください。

## 💌 連絡先

あなたの名前 - [@your_twitter](https://twitter.com/your_twitter) - email@example.com

プロジェクトリンク: [https://github.com/your-username/pycodelens](https://github.com/your-username/pycodelens)

---

<p align="center">
  <b>LLM開発コミュニティのために❤️を込めて作られました</b><br>
  <i>あなたのLLMにコード理解の贈り物を</i>
</p>
