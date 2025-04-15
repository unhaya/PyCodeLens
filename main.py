import ast
import astroid
import json
import os
import pickle
import re
import subprocess
import sys
import traceback

# サードパーティライブラリ
import pyperclip
from PIL import Image, ImageTk
from ttkthemes import ThemedTk
from tkinter import simpledialog

# tkinter 関連
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

class ConfigManager:
    """
    アプリケーションの設定を管理するクラス
    JSONファイルに設定を保存・読み込みする
    """
    def __init__(self, config_file=None):
        # 実行ファイルと同じディレクトリにconfigフォルダを作成して保存
        if config_file is None:
            # 実行ファイルのディレクトリを取得
            exe_dir = os.path.dirname(os.path.abspath(__file__))
            # configディレクトリのパス
            config_dir = os.path.join(exe_dir, "config")
            # 設定ファイルのパス
            self.config_file = os.path.join(config_dir, "code_analyzer_config.json")
            
            # configディレクトリが存在しない場合は作成
            if not os.path.exists(config_dir):
                try:
                    os.makedirs(config_dir, exist_ok=True)
                    print(f"設定ディレクトリを作成しました: {config_dir}")
                except Exception as e:
                    print(f"設定ディレクトリの作成に失敗しました: {e}")
                    # 失敗した場合はカレントディレクトリを使用
                    self.config_file = "code_analyzer_config.json"
        else:
            self.config_file = config_file
        
        # デフォルト設定
        self.config = {
            "last_directory": "",
            "last_file": "",
            "window_size": {"width": 800, "height": 600},
            "excluded_items": {}  # {"directory_path": {"item_path": True/False}}
        }
        
        # 設定ファイルの読み込み
        self.load_config()
    
    def load_config(self):
        """設定ファイルから設定を読み込む"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 読み込んだ設定でデフォルト設定を上書き
                    self.config.update(loaded_config)
                print(f"設定を読み込みました: {self.config_file}")
            else:
                print(f"設定ファイルが見つかりません。デフォルト設定を使用します。")
                # 初回起動時にデフォルト設定を保存
                self.save_config()
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
    
    def save_config(self):
        """設定をファイルに保存する"""
        try:
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir) and config_dir:
                try:
                    os.makedirs(config_dir, exist_ok=True)
                except Exception as e:
                    print(f"設定ディレクトリの作成に失敗しました: {e}")
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"設定を保存しました: {self.config_file}")
        except Exception as e:
            print(f"設定保存エラー: {e}")
            print(f"保存先パス: {self.config_file}")
            # エラー詳細を出力
            
            traceback.print_exc()
    
    def get_last_directory(self):
        """最後に選択したディレクトリを取得"""
        return self.config.get("last_directory", "")
    
    def set_last_directory(self, directory):
        """最後に選択したディレクトリを設定"""
        self.config["last_directory"] = directory
        self.save_config()
    
    def get_last_file(self):
        """最後に選択したファイルを取得"""
        return self.config.get("last_file", "")
    
    def set_last_file(self, file_path):
        """最後に選択したファイルを設定"""
        self.config["last_file"] = file_path
        self.save_config()
    
    def get_window_size(self):
        """ウィンドウサイズを取得"""
        return self.config.get("window_size", {"width": 1000, "height": 775})
    
    def set_window_size(self, width, height):
        """ウィンドウサイズを設定"""
        self.config["window_size"] = {"width": width, "height": height}
        self.save_config()

    def get_excluded_items(self, directory):
        """指定ディレクトリの除外アイテムを取得"""
        # ディレクトリパスを正規化
        directory = os.path.normpath(directory)
        excluded_items = self.config.get("excluded_items", {})
        return excluded_items.get(directory, {})

    def set_excluded_item(self, directory, item_path, is_excluded):
        """アイテムの除外状態を設定"""
        # ディレクトリとアイテムパスを正規化
        directory = os.path.normpath(directory)
        item_path = os.path.normpath(item_path)
        
        if "excluded_items" not in self.config:
            self.config["excluded_items"] = {}
        
        if directory not in self.config["excluded_items"]:
            self.config["excluded_items"][directory] = {}
        
        self.config["excluded_items"][directory][item_path] = is_excluded
        self.save_config()
    
    def clear_excluded_items(self, directory):
        """指定ディレクトリの除外アイテムをクリア"""
        if directory in self.config.get("excluded_items", {}):
            del self.config["excluded_items"][directory]
            self.save_config()

    def get_tab_selection(self):
        """タブ選択状態を取得"""
        return self.config.get("tab_selection", {
            "解析結果": False,
            "拡張解析": False,
            "プロンプト入力": False
        })

    def set_tab_selection(self, tab_selection):
        """タブ選択状態を設定"""
        self.config["tab_selection"] = tab_selection
        self.save_config()

class CodeAnalyzer:
    """
    Pythonコードを解析して、クラス名、関数名を抽出するクラス
    """
    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []
        self.report = ""
        self.char_count = 0
        self.include_imports = True
        self.include_docstrings = True 
    
    def reset(self):
        """解析結果をリセットする"""
        self.imports = []
        self.classes = []
        self.functions = []
        self.report = ""
        self.char_count = 0
    
    def analyze_file(self, file_path):
        """ファイルパスからコードを読み込んで解析する"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                code = file.read()
            return self.analyze_code(code, os.path.basename(file_path))
        except Exception as e:
            return f"ファイル解析エラー: {str(e)}", 0


    def analyze_files(self, file_paths):
        """複数のファイルを解析する"""
        self.reset()
        report_parts = []
        total_char_count = 0
        
        # ディレクトリ構造情報を生成
        all_dirs = set()
        for file_path in file_paths:
            dir_name = os.path.dirname(file_path)
            all_dirs.add(dir_name)
        
        # ディレクトリ構造をレポートに追加
        dir_structure = "# プロジェクト構造\n"
        root_dir = os.path.commonpath(list(all_dirs)) if all_dirs else ""
        if root_dir:
            dir_structure += f"ルートディレクトリ: {root_dir}\n"
            
            # サブディレクトリの一覧を表示
            for dir_path in sorted(all_dirs):
                rel_path = os.path.relpath(dir_path, root_dir)
                if rel_path != '.':  # ルートディレクトリ自体は除外
                    dir_structure += f"- {rel_path}/\n"
            
            dir_structure += "\n"
        
        report_parts.append(dir_structure)
        total_char_count += len(dir_structure)
        
        # 元の処理（ファイルごとの解析）を継続
        # ファイルをディレクトリごとにグループ化
        dir_files = {}
        for file_path in file_paths:
            dir_name = os.path.dirname(file_path)
            if dir_name not in dir_files:
                dir_files[dir_name] = []
            dir_files[dir_name].append(file_path)
        
        # ディレクトリごとに処理
        for dir_path, files in dir_files.items():
            # ディレクトリ名を追加
            dir_report = f"\n## ディレクトリ: {dir_path}\n"
            
            # Pythonファイルのみをフィルタリング
            py_files = [f for f in files if f.lower().endswith('.py')]
            
            # Pythonファイルがある場合のみ処理
            if py_files:
                # ディレクトリ内の各Pythonファイルを処理
                for file_path in sorted(py_files):
                    try:
                        file_name = os.path.basename(file_path)
                        
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code = f.read()
                        
                        # ファイルごとの解析結果
                        self.reset()
                        result, _ = self.analyze_code(code, file_name)
                        file_report = f"\n### ファイル: {file_name}\n"
                        file_report += result
                        
                        dir_report += file_report
                        total_char_count += len(file_report)
                    except Exception as e:
                        file_report = f"\n### ファイル: {os.path.basename(file_path)}\n解析エラー: {str(e)}\n"
                        dir_report += file_report
                        total_char_count += len(file_report)
            
            report_parts.append(dir_report)
        
        # すべてのディレクトリのレポートを結合
        self.report = "\n".join(report_parts)
        self.char_count = total_char_count
        return self.report, self.char_count

    def analyze_code(self, code, filename="", directory_structure=""):
        """Pythonコードを解析する"""
        self.reset()
        try:
            tree = ast.parse(code)
            
            # docstring（モジュールレベルのドキュメント文字列）を取得
            module_docstring = ast.get_docstring(tree)
            
            # インポート文を格納する辞書を初期化（モジュール名をキーとする）
            import_dict = {}
            
            # インポート文、クラス、関数を抽出
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if 'direct_import' not in import_dict:
                            import_dict['direct_import'] = []
                        import_dict['direct_import'].append(f"import {name.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if module not in import_dict:
                        import_dict[module] = []
                    for name in node.names:
                        import_dict[module].append(name.name)
                elif isinstance(node, ast.ClassDef):
                    class_methods = []
                    class_docstring = ast.get_docstring(node)
                    
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef):
                            method_docstring = ast.get_docstring(method)
                            # クラスメソッド内の関数を検索
                            inner_functions = []
                            for inner_node in ast.walk(method):
                                if isinstance(inner_node, ast.FunctionDef) and inner_node != method:
                                    inner_docstring = ast.get_docstring(inner_node)
                                    inner_functions.append({
                                        'name': inner_node.name,
                                        'docstring': inner_docstring
                                    })
                            
                            class_methods.append({
                                'name': method.name,
                                'docstring': method_docstring,
                                'inner_functions': inner_functions
                            })
                    
                    self.classes.append({
                        'name': node.name,
                        'docstring': class_docstring,
                        'methods': class_methods
                    })
                elif isinstance(node, ast.FunctionDef):
                    # トップレベルの関数かどうかをチェック（クラス内のメソッドではない）
                    function_docstring = ast.get_docstring(node)
                    
                    # すでに抽出したクラスメソッドの中に含まれていないかチェック
                    is_method = False
                    for cls in self.classes:
                        if any(method['name'] == node.name for method in cls['methods']):
                            is_method = True
                            break
                    
                    if not is_method:
                        # 関数内の関数を検索
                        inner_functions = []
                        for inner_node in ast.walk(node):
                            if isinstance(inner_node, ast.FunctionDef) and inner_node != node:
                                inner_docstring = ast.get_docstring(inner_node)
                                inner_functions.append({
                                    'name': inner_node.name,
                                    'docstring': inner_docstring
                                })
                        
                        self.functions.append({
                            'name': node.name,
                            'docstring': function_docstring,
                            'inner_functions': inner_functions
                        })
            
            # インポート辞書を整形された形式に変換
            self.imports = []
            for module, names in import_dict.items():
                if module == 'direct_import':
                    # 直接インポートは既にフォーマット済み
                    self.imports.extend(sorted(names))
                else:
                    # 同じモジュールからのインポートをまとめる
                    self.imports.append(f"from {module} import {', '.join(sorted(names))}")
            
            # ディレクトリ構造情報の追加
            self.directory_structure = directory_structure
            
            self.report = self.generate_report(filename)
            self.char_count = len(self.report)
            return self.report, self.char_count
        except SyntaxError as e:
            return f"構文エラー: {str(e)}", 0
        except Exception as e:
            return f"解析エラー: {str(e)}", 0
    
    def generate_report(self, filename=""):
        """解析結果からレポートを生成する"""
        report = ""
        
        # ディレクトリ構造情報があれば追加
        if hasattr(self, 'directory_structure') and self.directory_structure:
            report += "# ディレクトリ構造\n"
            report += self.directory_structure
            report += "\n\n"
        
        # インポート文を追加（フラグがTrueの場合のみ）
        if self.include_imports and self.imports:
            report += "# インポート\n"
            for import_stmt in self.imports:
                report += f"{import_stmt}\n"
            report += "\n"
        
        # クラスを追加
        if self.classes:
            report += "# クラス\n"
            for cls in self.classes:
                report += f"class {cls['name']}:\n"
                # クラスのdocstringを追加（フラグがTrueかつdocstringがある場合）
                if self.include_docstrings and cls['docstring']:
                    # 簡潔にするために1行目だけ表示
                    first_line = cls['docstring'].split('\n')[0].strip()
                    report += f"    \"{first_line}\"\n"
                
                # メソッドを追加
                if cls['methods']:
                    for method in cls['methods']:
                        report += f"    def {method['name']}()\n"
                        # メソッドのdocstringを追加（フラグがTrueかつdocstringがある場合）
                        if self.include_docstrings and method['docstring']:
                            first_line = method['docstring'].split('\n')[0].strip()
                            report += f"        \"{first_line}\"\n"
                        
                        # メソッド内の内部関数を追加
                        if 'inner_functions' in method and method['inner_functions']:
                            for inner_func in method['inner_functions']:
                                report += f"        def {inner_func['name']}()\n"
                                if self.include_docstrings and inner_func['docstring']:
                                    first_line = inner_func['docstring'].split('\n')[0].strip()
                                    report += f"            \"{first_line}\"\n"
                report += "\n"
        
        # 関数を追加
        if self.functions:
            report += "# 関数\n"
            for func in self.functions:
                report += f"def {func['name']}()\n"
                # 関数のdocstringを追加（フラグがTrueかつdocstringがある場合）
                if self.include_docstrings and func['docstring']:
                    first_line = func['docstring'].split('\n')[0].strip()
                    report += f"    \"{first_line}\"\n"
                
                # 関数内の内部関数を追加
                if 'inner_functions' in func and func['inner_functions']:
                    for inner_func in func['inner_functions']:
                        report += f"    def {inner_func['name']}()\n"
                        if self.include_docstrings and inner_func['docstring']:
                            first_line = inner_func['docstring'].split('\n')[0].strip()
                            report += f"        \"{first_line}\"\n"
            report += "\n"
            
        return report

def analyze_with_astroid(file_path):
    """指定したファイルをastroidで解析する簡易ヘルパー関数"""
    analyzer = AstroidAnalyzer()
    report, _ = analyzer.analyze_file(file_path)
    return report

class AstroidAnalyzer:
    """
    astroidを使用して、より深いコード解析を行うクラス
    型情報、継承関係、依存関係などの意味的な情報を抽出する
    """
    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []
        self.dependencies = {}  # 関数/メソッド間の依存関係
        self.inheritance = {}   # クラスの継承関係
        self.type_info = {}     # 変数・引数・戻り値の型情報
        self.report = ""
        self.char_count = 0

    def reset(self):
        """解析結果をリセットする"""
        self.imports = []
        self.classes = []
        self.functions = []
        self.dependencies = {}
        self.inheritance = {}
        self.type_info = {}
        self.report = ""
        self.char_count = 0

    def analyze_file(self, file_path):
        """ファイルパスからコードを読み込んで解析する"""
        try:
            
            with open(file_path, 'r', encoding='utf-8') as file:
                code = file.read()
            return self.analyze_code(code, os.path.basename(file_path))
        except ImportError:
            return "astroidライブラリがインストールされていません。pip install astroid でインストールしてください。", 0
        except Exception as e:
            return f"ファイル解析エラー: {str(e)}", 0

    def analyze_code(self, code, filename=""):
        """astroidを使ってPythonコードを解析する"""
        self.reset()
        try:
            
            tree = astroid.parse(code)
            
            # モジュールレベルのドキュメント文字列
            module_docstring = tree.doc_node.value if tree.doc_node else None
            
            # インポート文を解析
            self._extract_imports(tree)
            
            # クラスと関数を解析
            for node in tree.body:
                if isinstance(node, astroid.ClassDef):
                    self._analyze_class(node)
                elif isinstance(node, astroid.FunctionDef):
                    self._analyze_function(node)
            
            # 継承関係と依存関係を解析
            self._analyze_dependencies(tree)
            
            # レポート生成
            self.report = self.generate_report(filename)
            self.char_count = len(self.report)
            return self.report, self.char_count
            
        except ImportError:
            return "astroidライブラリがインストールされていません。pip install astroid でインストールしてください。", 0
        except Exception as e:
            return f"解析エラー: {str(e)}", 0
            
    def _extract_imports(self, tree):
        """インポート文を抽出して解析する"""
        
        for node in tree.body:
            if isinstance(node, astroid.Import):
                for name in node.names:
                    self.imports.append(f"import {name[0]}")
            elif isinstance(node, astroid.ImportFrom):
                module = node.modname
                names = [name[0] for name in node.names]
                self.imports.append(f"from {module} import {', '.join(names)}")

    def _analyze_dependencies(self, tree):
        """関数間やクラス間の依存関係を解析する（エラー処理強化版）"""
        
        
        try:
            # 関数呼び出しを検出して依存関係を構築
            for node in tree.body:
                try:
                    if isinstance(node, astroid.FunctionDef):
                        self._find_dependencies(node, node.name)
                    elif isinstance(node, astroid.ClassDef):
                        for method in node.body:
                            if isinstance(method, astroid.FunctionDef):
                                self._find_dependencies(method, f"{node.name}.{method.name}")
                except Exception as e:
                    print(f"依存関係解析中にエラー ({getattr(node, 'name', 'unknown')}): {e}")
        except Exception as e:
            print(f"依存関係全体の解析中にエラー: {e}")

    def _find_dependencies(self, node, caller_name):
        """ノード内の関数呼び出しを検出して依存関係を記録する（エラー処理強化版）"""
        
        
        try:
            if caller_name not in self.dependencies:
                self.dependencies[caller_name] = set()
            
            # get_childrenはエラーを起こす可能性があるので安全に処理
            try:
                children = list(node.get_children())
            except Exception:
                children = []
                
            for child in children:
                try:
                    if isinstance(child, astroid.Call):
                        try:
                            if isinstance(child.func, astroid.Name):
                                self.dependencies[caller_name].add(child.func.name)
                            elif isinstance(child.func, astroid.Attribute):
                                # 安全に属性参照を取得
                                if isinstance(child.func.expr, astroid.Name):
                                    self.dependencies[caller_name].add(f"{child.func.expr.name}.{child.func.attrname}")
                        except Exception as e:
                            print(f"関数呼び出し解析中にエラー: {e}")
                    
                    # 再帰的に子ノードも調査（子ノードがエラーでも中断しない）
                    try:
                        self._find_dependencies(child, caller_name)
                    except Exception as e:
                        print(f"依存関係の再帰処理中にエラー: {e}")
                except Exception as e:
                    print(f"子ノード処理中にエラー: {e}")
        except Exception as e:
            print(f"依存関係検索中にエラー ({caller_name}): {e}")

    def _analyze_function(self, node, is_inner=False):
        """トップレベルまたは内部関数を解析する"""
        
        
        try:
            # 基本情報
            func_info = {
                'name': node.name,
                'docstring': node.doc_node.value if hasattr(node, 'doc_node') and node.doc_node else None,
                'parameters': [],
                'return_type': None,
                'inner_functions': []
            }
            
            # 引数の解析
            try:
                if hasattr(node, 'args') and hasattr(node.args, 'args'):
                    for arg in node.args.args:
                        param_name = getattr(arg, 'name', 'unknown')
                        param_info = {'name': param_name}
                        
                        # 型アノテーションがある場合（安全にチェック）
                        try:
                            if hasattr(arg, 'annotation') and arg.annotation:
                                param_info['type'] = self._get_annotation_name(arg.annotation)
                        except Exception:
                            # 型注釈の取得に失敗した場合は無視
                            pass
                            
                        func_info['parameters'].append(param_info)
            except Exception as e:
                print(f"関数引数の解析中にエラー: {e}")
            
            # 戻り値の型アノテーション（安全にチェック）
            try:
                if hasattr(node, 'returns') and node.returns:
                    func_info['return_type'] = self._get_annotation_name(node.returns)
                else:
                    # 戻り値の型を推論
                    func_info['return_type'] = self._infer_return_type(node)
            except Exception as e:
                print(f"関数の戻り値型解析中にエラー: {e}")
                func_info['return_type'] = "unknown"
            
            # 内部関数を解析
            try:
                for child in node.body:
                    if isinstance(child, astroid.FunctionDef):
                        try:
                            inner_func = self._analyze_function(child, is_inner=True)
                            func_info['inner_functions'].append(inner_func)
                        except Exception as e:
                            print(f"内部関数 {getattr(child, 'name', 'unknown')} の解析中にエラー: {e}")
            except Exception as e:
                print(f"関数内の内部関数走査中にエラー: {e}")
            
            # 内部関数でない場合はfunctionsリストに追加
            if not is_inner:
                self.functions.append(func_info)
            
            return func_info
        except Exception as e:
            print(f"関数 {getattr(node, 'name', 'unknown')} の解析中に例外が発生: {e}")
            # 最低限の情報を含む空の関数情報を返す
            return {'name': getattr(node, 'name', 'unknown'), 'parameters': [], 'inner_functions': []}

    def _analyze_method(self, node):
        """クラスメソッドを解析する"""
        
        
        try:
            # 基本情報
            method_info = {
                'name': node.name,
                'docstring': node.doc_node.value if hasattr(node, 'doc_node') and node.doc_node else None,
                'parameters': [],
                'return_type': None,
                'inner_functions': []
            }
            
            # 引数の解析
            try:
                if hasattr(node, 'args') and hasattr(node.args, 'args'):
                    for arg in node.args.args:
                        if arg.name == 'self':
                            continue  # selfパラメータはスキップ
                            
                        param_name = getattr(arg, 'name', 'unknown')
                        param_info = {'name': param_name}
                        
                        # 型アノテーションがある場合（安全にチェック）
                        try:
                            if hasattr(arg, 'annotation') and arg.annotation:
                                param_info['type'] = self._get_annotation_name(arg.annotation)
                        except Exception:
                            # 型注釈の取得に失敗した場合は無視
                            pass
                                
                        method_info['parameters'].append(param_info)
            except Exception as e:
                print(f"メソッド引数の解析中にエラー: {e}")
            
            # 戻り値の型アノテーション（安全にチェック）
            try:
                if hasattr(node, 'returns') and node.returns:
                    method_info['return_type'] = self._get_annotation_name(node.returns)
                else:
                    # 戻り値の型を推論
                    method_info['return_type'] = self._infer_return_type(node)
            except Exception as e:
                print(f"メソッドの戻り値型解析中にエラー: {e}")
                method_info['return_type'] = "unknown"
            
            # 内部関数を解析
            try:
                for child in node.body:
                    if isinstance(child, astroid.FunctionDef):
                        try:
                            inner_func = self._analyze_function(child, is_inner=True)
                            method_info['inner_functions'].append(inner_func)
                        except Exception as e:
                            print(f"メソッド内の内部関数 {getattr(child, 'name', 'unknown')} の解析中にエラー: {e}")
            except Exception as e:
                print(f"メソッド内の内部関数走査中にエラー: {e}")
            
            return method_info
            
        except Exception as e:
            print(f"メソッド {getattr(node, 'name', 'unknown')} の解析中に例外が発生: {e}")
            # 最低限の情報を含む空のメソッド情報を返す
            return {'name': getattr(node, 'name', 'unknown'), 'parameters': [], 'inner_functions': []}

    def _get_annotation_name(self, annotation):
        """型アノテーションノードから型名を取得する（エラー処理強化版）"""
        
        
        try:
            if isinstance(annotation, astroid.Name):
                return annotation.name
            elif isinstance(annotation, astroid.Attribute):
                # 安全に属性参照を取得
                expr_name = "unknown"
                try:
                    if hasattr(annotation.expr, 'name'):
                        expr_name = annotation.expr.name
                except:
                    pass
                return f"{expr_name}.{annotation.attrname}"
            elif isinstance(annotation, astroid.Subscript):
                # ジェネリック型（List[str]など）
                value_name = "unknown"
                try:
                    value_name = self._get_annotation_name(annotation.value)
                except:
                    pass
                    
                # ジェネリック型のパラメータの取得（バージョン間の違いに対応）
                try:
                    # astroid 2.x系
                    if hasattr(annotation, 'slice') and hasattr(annotation.slice, 'value'):
                        slice_value = annotation.slice.value
                        if isinstance(slice_value, astroid.Name):
                            return f"{value_name}[{slice_value.name}]"
                        elif isinstance(slice_value, astroid.Tuple):
                            elts = []
                            for elt in slice_value.elts:
                                if isinstance(elt, astroid.Name):
                                    elts.append(elt.name)
                            return f"{value_name}[{', '.join(elts)}]"
                    # astroid 2.0以前または異なる構造
                    elif hasattr(annotation, 'slice'):
                        return f"{value_name}[...]"
                except:
                    # どのパターンにも一致しない場合は簡略化した形式を返す
                    return f"{value_name}[?]"
                    
                # どれにも一致しない場合
                return value_name
            # その他の型は文字列化して返す
            return str(type(annotation).__name__)
        except Exception as e:
            print(f"型アノテーション解析中にエラー: {e}")
            return "unknown"

    def _infer_type(self, node):
        """ノードから型を推論する（エラー処理強化版）"""
        try:
            if node is None:
                return "unknown"
                
            # SafeInferの使用を検討
            inferred = list(node.infer())
            if not inferred:
                return "unknown"
                
            # 推論結果の最初の要素を使用
            first = inferred[0]
            
            if hasattr(first, "pytype"):
                pytype = first.pytype()
                return pytype.split(".")[-1]
            else:
                return type(first).__name__
        except StopIteration:
            # StopIterationを捕捉して適切に処理
            return "unknown"
        except Exception as e:
            print(f"型推論エラー: {str(e)}")
            return "unknown"

    def _infer_return_type(self, node):
        """関数の戻り値の型を推論する（エラー処理強化版）"""
        types = set()
        return_values = []
        
        try:
            # return文を探す
            for child_node in node.get_children():
                if isinstance(child_node, astroid.Return) and child_node.value:
                    return_values.append(child_node.value)
            
            # 各return文の型を推論
            for return_node in return_values:
                try:
                    inferred = list(return_node.infer())
                    if inferred:
                        for inf in inferred:
                            if hasattr(inf, "pytype"):
                                types.add(inf.pytype().split(".")[-1])
                            else:
                                types.add(type(inf).__name__)
                except StopIteration:
                    # StopIterationをここで処理
                    continue
                except Exception as e:
                    print(f"戻り値型推論エラー: {str(e)}")
                    continue
                    
            if len(types) == 0:
                return "None"
            elif len(types) == 1:
                return list(types)[0]
            else:
                return " | ".join(sorted(types))
        except Exception as e:
            print(f"戻り値型推論全体エラー: {str(e)}")
            return "unknown"   
            
    def _find_dependencies(self, node, caller_name):
        """ノード内の関数呼び出しを検出して依存関係を記録する"""
        
        
        if caller_name not in self.dependencies:
            self.dependencies[caller_name] = set()
        
        for child in node.get_children():
            if isinstance(child, astroid.Call):
                if isinstance(child.func, astroid.Name):
                    self.dependencies[caller_name].add(child.func.name)
                elif isinstance(child.func, astroid.Attribute):
                    if isinstance(child.func.expr, astroid.Name):
                        self.dependencies[caller_name].add(f"{child.func.expr.name}.{child.func.attrname}")
            
            # 再帰的に子ノードも調査
            self._find_dependencies(child, caller_name)
    
    def generate_report(self, filename=""):
        """解析結果からわかりやすいレポートを生成する（必要な情報のみ）"""
        report = ""
        
        # ファイル名
        if filename:
            report += f"# {filename} の解析レポート\n\n"
        else:
            report += "# Pythonコード解析レポート\n\n"
        
        # インポート文は除外 (冗長情報)
        
        # プロジェクト構造 (重要情報1)
        # この部分はディレクトリ情報から生成されるため、ここでは変更なし
        
        # クラス階層図 (重要情報2)
        if self.classes:
            report += "## クラス階層図\n"
            for cls in self.classes:
                if cls['base_classes']:
                    report += f"- **{cls['name']}** ← {', '.join(cls['base_classes'])}\n"
                else:
                    report += f"- **{cls['name']}**\n"
            report += "\n"
        
        # ファイル間の依存関係 - シンプルに保持
        if self.inheritance:
            report += "## ファイル間の依存関係\n"
            # ここは重要なファイル間の依存関係のみを表示するよう変更
            report += "- **<ファイル名>.py** (依存なし)\n" # 必要に応じて実際の依存関係を表示
            report += "\n"
        
        # 各クラスのメソッド一覧 (重要情報3)
        if self.classes:
            report += "## ファイルごとの詳細情報\n"
            if filename:
                report += f"### {filename}\n"
                
            report += "**クラス:**\n"
            for cls in self.classes:
                base_classes = f" (継承: {', '.join(cls['base_classes'])})" if cls['base_classes'] else ""
                report += f"- `{cls['name']}`{base_classes}\n"
                
                # メソッド（シンプルに名前のみ表示）
                if cls['methods']:
                    report += "  **メソッド:**\n"
                    for method in cls['methods']:
                        report += f"  - `{method['name']}`\n"
            report += "\n"
        
        # トップレベル関数リスト（シンプルに表示）
        if self.functions:
            report += "**関数:**\n"
            for func in self.functions:
                report += f"- `{func['name']}`\n"
            report += "\n"
        
        # LLM向け構造化データ (重要情報4)
        report += "## LLM向け構造化データ\n"
        report += "```\n"
        # コンパクトなフォーマットでデータを出力
        compact_data = "# クラス一覧\n"
        for cls in self.classes:
            base_info = f" <- {', '.join(cls['base_classes'])}" if cls['base_classes'] else ""
            compact_data += f"{cls['name']}{base_info}\n"

            if cls['methods']:
                compact_data += "  メソッド:\n"
                for m in cls['methods']:
                    params = ", ".join(p['name'] for p in m['parameters'])
                    ret_type = f" -> {m['return_type']}" if m['return_type'] and m['return_type'] != "unknown" else ""
                    compact_data += f"    {m['name']}({params}){ret_type}\n"
            compact_data += "\n"
        compact_data += "# 関数一覧\n"
        for func in self.functions:
            params = ", ".join(p['name'] for p in func['parameters'])
            ret_type = f" -> {func['return_type']}" if func['return_type'] and func['return_type'] != "unknown" else ""
            compact_data += f"{func['name']}({params}){ret_type}\n"
        compact_data += "\n"
        # 主要な依存関係のみ表示
        if self.dependencies:
            compact_data += "# 主要な依存関係\n"
            for caller, callees in self.dependencies.items():
                if callees:  # 空でない場合のみ
                    compact_data += f"{caller} -> {', '.join(callees)}\n"
            compact_data += "\n"
        report += compact_data
        report += "```\n"



        
    def _analyze_class(self, node):
        """クラス定義を解析する（エラー処理強化版）"""
        
        
        try:
            # 基本情報の取得
            class_info = {
                'name': node.name,
                'docstring': node.doc_node.value if hasattr(node, 'doc_node') and node.doc_node else None,
                'methods': [],
                'base_classes': [],
                'attributes': []
            }
            
            # 継承関係を解析
            try:
                for base in node.bases:
                    if isinstance(base, astroid.Name):
                        class_info['base_classes'].append(base.name)
                    elif isinstance(base, astroid.Attribute):
                        base_expr_name = getattr(base.expr, 'name', 'unknown')
                        class_info['base_classes'].append(f"{base_expr_name}.{base.attrname}")
            except Exception as e:
                print(f"継承関係の解析中にエラー: {e}")
            
            # 継承関係を記録
            self.inheritance[node.name] = class_info['base_classes']
            
            # メソッドとクラス変数を解析
            for child in node.body:
                try:
                    if isinstance(child, astroid.FunctionDef):
                        method_info = self._analyze_method(child)
                        class_info['methods'].append(method_info)
                    elif isinstance(child, astroid.Assign):
                        for target in child.targets:
                            if isinstance(target, astroid.AssignName):
                                # クラス変数を記録（安全に型を推論）
                                attr_type = "unknown"
                                try:
                                    attr_type = self._infer_type(child.value)
                                except Exception as e:
                                    print(f"属性型推論エラー: {e}")
                                
                                class_info['attributes'].append({
                                    'name': target.name,
                                    'type': attr_type
                                })
                except Exception as e:
                    print(f"クラス内のノード解析中にエラー: {e}")
                    continue
            
            self.classes.append(class_info)
            return class_info
        except Exception as e:
            print(f"クラス {getattr(node, 'name', 'unknown')} の解析中に例外が発生: {e}")
            # 最低限の情報を含む空のクラス情報を返す
            return {'name': getattr(node, 'name', 'unknown'), 'methods': [], 'base_classes': [], 'attributes': []}

class DirectoryTreeView:
    """ディレクトリとファイルをツリー表示するクラス（カラーアイコン付き）"""
    def __init__(self, parent, config_manager):
        self.parent = parent
        
        # 設定マネージャーを保存
        self.config_manager = config_manager
        
        # アイコン画像の読み込み
        self.load_icons()
        
        # ツリービューの作成
        self.tree = ttk.Treeview(parent)
        self.tree.pack(side=tk.LEFT, expand=True, fill="both")
        
        # スクロールバーの追加
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # ツリービューのカラム設定（status列を非表示に）
        self.tree["columns"] = ()
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.heading("#0", text="  file/folder", anchor="w")
        
        # 除外リスト
        self.excluded_items = set()
        
        # 処理中フラグ（処理の重複実行を防止）
        self.is_processing = False
        
        # イベントバインド
        self.tree.bind("<Control-Button-1>", self.toggle_exclusion)  # Ctrl+クリック
        self.tree.bind("<Double-1>", self.on_item_double_click)  # ダブルクリック
        
        # 右クリックメニューの設定
        self.setup_context_menu()
        
        # 現在のディレクトリパス
        self.current_dir = None
        
        # ステータステキスト - カラーラベルつき（処理内部で利用するため残す）
        self.included_text = "✓ 含む"
        self.excluded_text = "✗ 除外"
        
        # 選択されたファイル（ダブルクリック用）
        self.selected_file = None
        
        # 選択されたディレクトリ
        self.selected_dir = None
        
        # ファイル選択コールバック
        self.on_file_selected = None
        
        # ディレクトリ選択コールバック
        self.on_dir_selected = None
        
        # 最大処理アイテム数
        self.max_items_to_process = 1000
        
        # 追加: スキップするファイル拡張子のリスト
        self.skip_extensions = ['.exe', '.dll', '.bin', '.so', '.pyc', '.pyd']
        
        # 追加: スキップするフォルダ名のリスト
        self.skip_folders = ['__pycache__', 'node_modules', 'build', 'dist', 'venv', 'env', '.git', '.idea', '.vscode']
        
        # 追加: EXEファイルが含まれるフォルダをスキップするかどうかのフラグ
        self.skip_exe_folders = True
    
    def load_icons(self):
        """アイコン画像を読み込む（複数の候補パスから検索する改良版）"""
        # デフォルトアイコンを設定（PILがない場合や画像が見つからない場合用）
        self.folder_icon = None
        self.file_icon = None
        self.locked_folder_icon = None
        self.locked_file_icon = None
        
        try:
            # PILをインポート（ない場合はテキストアイコンを使用）
            from PIL import Image, ImageTk
            
            # アイコンを探す複数の候補パスを設定
            icon_paths = []
            
            # 1. 実行ファイルと同じディレクトリのiconフォルダ
            exe_dir = os.path.dirname(os.path.abspath(__file__))
            icon_paths.append(os.path.join(exe_dir, "icon"))
            
            # 2. カレントディレクトリのiconフォルダ
            icon_paths.append(os.path.join(os.getcwd(), "icon"))
            
            # 3. PyInstallerでexe化された場合のパス
            try:
                import sys
                if getattr(sys, 'frozen', False):
                    # PyInstaller環境
                    exe_path = sys._MEIPASS
                    icon_paths.append(os.path.join(exe_path, "icon"))
            except (AttributeError, ImportError):
                pass
            
            # 4. 親ディレクトリのiconフォルダ
            icon_paths.append(os.path.join(os.path.dirname(exe_dir), "icon"))
            
            # 5. 以前指定されていたパス（後方互換性のため）
            alt_icon_dir = r"D:\OneDrive\In the middle of an update\code_analysis\icon"
            icon_paths.append(alt_icon_dir)
            
            # アイコンファイル名のバリエーション
            folder_filenames = ["folder.png", "icons8-フォルダ-48.png", "folder_icon.png", "directory.png"]
            file_filenames = ["file.png", "icons8-資料-48.png", "file_icon.png", "document.png"]
            
            # アイコンを見つける
            folder_path = None
            file_path = None
            
            # 各候補パスとファイル名の組み合わせを試す
            for icon_dir in icon_paths:
                if not os.path.exists(icon_dir):
                    continue
                    
                # フォルダアイコンの検索
                for fname in folder_filenames:
                    path = os.path.join(icon_dir, fname)
                    if os.path.exists(path):
                        folder_path = path
                        break
                
                # ファイルアイコンの検索
                for fname in file_filenames:
                    path = os.path.join(icon_dir, fname)
                    if os.path.exists(path):
                        file_path = path
                        break
                
                # 両方見つかったら終了
                if folder_path and file_path:
                    break
            
            # アイコンが見つからない場合は早期リターン
            if not folder_path or not file_path:
                print("アイコンが見つかりませんでした。テキストアイコンを使用します。")
                return
            
            # 見つかったアイコンを読み込む
            # フォルダアイコン
            original_folder = Image.open(folder_path)
            resized_folder = original_folder.resize((24, 24), Image.LANCZOS)
            self.folder_icon = ImageTk.PhotoImage(resized_folder)
            
            # ファイルアイコン
            original_file = Image.open(file_path)
            resized_file = original_file.resize((24, 24), Image.LANCZOS)
            self.file_icon = ImageTk.PhotoImage(resized_file)
            
            # ロックされたフォルダアイコン（グレースケール）
            locked_folder = resized_folder.convert("L").convert("RGBA")
            self.locked_folder_icon = ImageTk.PhotoImage(locked_folder)
            
            # ロックされたファイルアイコン（グレースケール）
            locked_file = resized_file.convert("L").convert("RGBA")
            self.locked_file_icon = ImageTk.PhotoImage(locked_file)
            
            print(f"アイコンを正常に読み込みました。フォルダ: {folder_path}, ファイル: {file_path}")
        except ImportError:
            print("PILライブラリがインストールされていません。テキストアイコンを使用します。")
        except Exception as e:
            print(f"アイコンの読み込みエラー: {e}")
            # エラーが発生した場合はテキストアイコンを使用

    def set_file_selected_callback(self, callback):
        """ファイル選択時のコールバック関数を設定"""
        self.on_file_selected = callback

    def set_dir_selected_callback(self, callback):
        """ディレクトリ選択時のコールバック関数を設定"""
        self.on_dir_selected = callback

    def setup_context_menu(self):
        """右クリックメニューの設定"""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        
        # メニュー項目の追加
        self.context_menu.add_command(label="エクスプローラーで開く", command=self.open_in_explorer)
        self.context_menu.add_command(label="デフォルトアプリで開く", command=self.open_with_default_app)
        # 含む/除外のメニュー項目は非表示
        
        # 右クリックイベントをバインド
        if sys.platform == 'darwin':  # macOS
            self.tree.bind("<Button-2>", self.show_context_menu)
        else:  # Windows/Linux
            self.tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """コンテキストメニューを表示"""
        # クリックされた項目を特定
        item_id = self.tree.identify_row(event.y)
        if item_id:
            # 項目を選択
            self.tree.selection_set(item_id)
            # アイテムパスを取得
            item_path = self.get_item_path(item_id)
            
            # ファイルまたはディレクトリによってメニュー項目を有効/無効化
            is_dir = os.path.isdir(item_path) if item_path else False
            
            # デフォルトアプリで開くメニューをファイルの場合のみ有効化
            self.context_menu.entryconfig("デフォルトアプリで開く", state=tk.NORMAL if not is_dir else tk.DISABLED)
            
            # メニューを表示
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def open_in_explorer(self):
        """選択したアイテムをエクスプローラーで開く"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        item_path = self.get_item_path(selected_items[0])
        if not item_path:
            return
        
        # ディレクトリでない場合は親ディレクトリを取得
        if not os.path.isdir(item_path):
            item_path = os.path.dirname(item_path)
        
        # OSに応じてファイルマネージャーを開く
        if sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', item_path])
        elif sys.platform == 'win32':  # Windows
            subprocess.Popen(['explorer', item_path])
        else:  # Linux
            try:
                subprocess.Popen(['xdg-open', item_path])
            except:
                # 失敗した場合は一般的なファイラーを試す
                try:
                    subprocess.Popen(['nautilus', item_path])
                except:
                    try:
                        subprocess.Popen(['thunar', item_path])
                    except:
                        messagebox.showinfo("情報", f"'{item_path}'を開けませんでした。")
    
    def open_with_default_app(self):
        """選択したファイルをデフォルトアプリで開く"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        item_path = self.get_item_path(selected_items[0])
        if not item_path or os.path.isdir(item_path):
            return
        
        # OSに応じてデフォルトアプリでファイルを開く
        if sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', item_path])
        elif sys.platform == 'win32':  # Windows
            os.startfile(item_path)
        else:  # Linux
            try:
                subprocess.Popen(['xdg-open', item_path])
            except:
                messagebox.showinfo("情報", f"'{item_path}'を開けませんでした。")
    
    def include_selected(self):
        """選択したアイテムを解析に含める"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item_id in selected_items:
            if item_id in self.excluded_items:
                # 含む状態に切り替え
                event = type('Event', (), {'y': self.tree.bbox(item_id)[1] + 5})()
                self.toggle_exclusion(event)
    
    def exclude_selected(self):
        """選択したアイテムを解析から除外"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        for item_id in selected_items:
            if item_id not in self.excluded_items:
                # 除外状態に切り替え
                event = type('Event', (), {'y': self.tree.bbox(item_id)[1] + 5})()
                self.toggle_exclusion(event)
    
    def on_item_double_click(self, event):
        """ツリーアイテムがダブルクリックされたときの処理"""
        if not hasattr(self, 'tree') or not self.tree or not self.tree.winfo_exists():
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # アイテムがディレクトリか確認
        is_dir = len(self.tree.get_children(item_id)) > 0
        if is_dir:
            # ディレクトリの場合は開閉を切り替え
            if self.tree.item(item_id, "open"):
                self.tree.item(item_id, open=False)
            else:
                self.tree.item(item_id, open=True)
            
            # ディレクトリパスを取得
            dir_path = self.get_item_path(item_id)
            if dir_path and os.path.isdir(dir_path):
                # 現在の選択状態を保存
                self.selected_dir = dir_path
                
                # ディレクトリ選択コールバックを呼び出す
                if self.on_dir_selected:
                    self.on_dir_selected(dir_path)
            return

        # ファイルの場合はパスを取得
        full_path = self.get_item_path(item_id)
        if full_path and full_path.endswith('.py'):
            print(f"ファイル選択: {full_path}")  # デバッグ用
            self.selected_file = full_path
            
            # 設定に保存
            self.config_manager.set_last_file(full_path)
            
            if self.on_file_selected:
                self.on_file_selected(full_path)

    def get_item_path(self, item_id):
        """ツリーアイテムのフルパスを取得（階層の深さに関わらず）"""
        if not self.current_dir or not item_id:
            return None
        
        # ルートノードかチェック
        if item_id == self.tree.get_children("")[0]:
            return self.current_dir
        
        path_parts = []
        current = item_id
        
        # 親アイテムを辿ってパスを構築
        while current:
            item_text = self.tree.item(current, "text").strip()
            # 先頭の絵文字やスペースを削除
            if item_text.startswith("📁 ") or item_text.startswith("🐍 ") or item_text.startswith("🔒 ") or item_text.startswith("📄 "):
                item_text = item_text[2:].strip()
            elif " " in item_text and item_text[0] != " ":
                # 先頭が絵文字の場合（フォーマットが " 名前"）
                item_text = item_text.split(" ", 1)[1].strip()
            
            # ルートノードに達したかチェック
            if current == self.tree.get_children("")[0]:
                break
            
            # 空でないテキストのみ追加
            if item_text:
                path_parts.insert(0, item_text)
            
            parent = self.tree.parent(current)
            if not parent:
                break
            
            current = parent
        
        # カレントディレクトリをベースにパスを構築
        full_path = os.path.normpath(os.path.join(self.current_dir, *path_parts))
        return full_path
   
    def toggle_exclusion(self, event):
        """Ctrl+クリックで項目の除外/含むを切り替え（エラーハンドリング追加）"""
        # すでに処理中の場合は新たな操作を受け付けない
        if self.is_processing:
            messagebox.showinfo("情報", "現在処理中です。しばらくお待ちください。")
            return
            
        try:
            # 処理中フラグをセット
            self.is_processing = True
            
            # クリックされた項目を特定
            item_id = self.tree.identify_row(event.y)
            if not item_id:
                self.is_processing = False
                return
            
            # 現在の状態を確認（excluded_itemsセットの有無で判断）
            is_excluded = item_id in self.excluded_items
            
            # アイテムのパスを取得し正規化
            item_path = self.get_item_path(item_id)
            if not item_path:
                self.is_processing = False
                return
            
            item_path = os.path.normpath(item_path)
            print(f"切り替えるアイテムのパス: {item_path}")  # デバッグ用
            
            # 子アイテムの数を事前に確認
            child_count = self._count_children(item_id)
            
            # 子アイテムが多すぎる場合は確認
            if child_count > self.max_items_to_process:
                confirm = messagebox.askyesno(
                    "確認", 
                    f"このフォルダには{child_count}個の項目が含まれています。\n"
                    "処理に時間がかかる可能性があります。続行しますか？"
                )
                if not confirm:
                    self.is_processing = False
                    return
            
            # バックグラウンド処理のためのプログレスバーを表示
            if child_count > 100:
                progress_window = tk.Toplevel(self.parent)
                progress_window.title("処理中")
                progress_window.geometry("300x100")
                progress_window.resizable(False, False)
                progress_window.transient(self.parent)
                
                progress_label = ttk.Label(progress_window, text=f"項目を処理中... (0/{child_count})")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, mode="determinate", maximum=100)
                progress_bar.pack(fill="x", padx=20)
                
                # ウィンドウを画面中央に配置
                progress_window.update_idletasks()
                x = self.parent.winfo_rootx() + (self.parent.winfo_width() - progress_window.winfo_width()) // 2
                y = self.parent.winfo_rooty() + (self.parent.winfo_height() - progress_window.winfo_height()) // 2
                progress_window.geometry(f"+{x}+{y}")
            else:
                progress_window = None
                progress_label = None
                progress_bar = None
            
            # UI更新を実行
            self._update_exclusion_status(item_id, is_excluded, progress_window, progress_label, progress_bar)
            
        except Exception as e:
            messagebox.showerror("エラー", f"処理中にエラーが発生しました: {str(e)}")
            
            traceback.print_exc()
        finally:
            self.is_processing = False
    
    def _update_exclusion_status(self, item_id, is_excluded, progress_window=None, progress_label=None, progress_bar=None):
        """項目の除外状態を更新（バックグラウンド処理）"""
        # 項目のパスを取得
        item_path = self.get_item_path(item_id)
        
        if not is_excluded:  # 現在含む状態 → 除外状態に変更
            # 空のvaluesを設定
            self.tree.item(item_id, values=())
            self.excluded_items.add(item_id)
            
            # 設定に状態を保存
            self.config_manager.set_excluded_item(self.current_dir, item_path, True)
            
            # アイコンを変更
            is_dir = len(self.tree.get_children(item_id)) > 0
            if is_dir and self.locked_folder_icon:
                self.tree.item(item_id, image=self.locked_folder_icon)
            elif not is_dir and self.locked_file_icon:
                self.tree.item(item_id, image=self.locked_file_icon)
            else:
                # アイコンが使えない場合はテキストを変更
                text = self.tree.item(item_id, "text")
                if "📁" in text:
                    self.tree.item(item_id, text=text.replace("📁", "🔒"))
                elif "🐍" in text or "📄" in text:
                    self.tree.item(item_id, text=text.replace("🐍", "🔒").replace("📄", "🔒"))
            
            # セルの背景色を変更
            self.tree.tag_configure('excluded', foreground='#999999')
            self.tree.item(item_id, tags=('excluded',))
            
            # 子アイテムも全て除外
            self._set_children_status_with_progress(item_id, "exclude", progress_window, progress_label, progress_bar)
        else:  # 現在除外状態 → 含む状態に変更
            # 空のvaluesを設定
            self.tree.item(item_id, values=())
            
            # 設定に状態を保存
            self.config_manager.set_excluded_item(self.current_dir, item_path, False)
            
            # アイコンを戻す
            is_dir = len(self.tree.get_children(item_id)) > 0
            if is_dir and self.folder_icon:
                self.tree.item(item_id, image=self.folder_icon)
            elif not is_dir and self.file_icon:
                self.tree.item(item_id, image=self.file_icon)
            else:
                # アイコンが使えない場合はテキストを変更
                text = self.tree.item(item_id, "text")
                if "🔒" in text:
                    if is_dir:
                        self.tree.item(item_id, text=text.replace("🔒", "📁"))
                    else:
                        # ファイル拡張子を確認
                        file_ext = os.path.splitext(item_path)[1].lower()
                        if file_ext == '.py':
                            self.tree.item(item_id, text=text.replace("🔒", "🐍"))
                        else:
                            self.tree.item(item_id, text=text.replace("🔒", "📄"))
            
            # セルの背景色を元に戻す
            self.tree.item(item_id, tags=())
            
            if item_id in self.excluded_items:
                self.excluded_items.remove(item_id)
            
            # 子アイテムも全て含む
            self._set_children_status_with_progress(item_id, "include", progress_window, progress_label, progress_bar)
        
        # プログレスウィンドウを閉じる
        if progress_window and progress_window.winfo_exists():
            progress_window.destroy()
    
    def _count_children(self, item_id, count=0):
        """アイテムの子アイテム数を再帰的にカウント"""
        children = self.tree.get_children(item_id)
        count += len(children)
        
        for child_id in children:
            count = self._count_children(child_id, count)
        
        return count
    
    def _set_children_status_with_progress(self, parent_id, status, progress_window=None, progress_label=None, progress_bar=None):
        """子アイテムのステータスを再帰的に設定（プログレス表示付き）"""
        children = self.tree.get_children(parent_id)
        total_children = len(children)
        
        # 子ノードがなければ何もしない
        if total_children == 0:
            return
        
        # プログレスバーの更新間隔（子アイテムが多い場合は更新頻度を下げる）
        if total_children > 1000:
            update_interval = 100
        elif total_children > 100:
            update_interval = 20
        else:
            update_interval = 5
        
        for i, child_id in enumerate(children):
            # プログレス表示の更新
            if progress_window and i % update_interval == 0:
                if not progress_window.winfo_exists():
                    return  # ウィンドウが閉じられた場合は処理を中断
                
                progress_pct = (i / total_children) * 100
                progress_bar["value"] = progress_pct
                progress_label.config(text=f"項目を処理中... ({i}/{total_children})")
                progress_window.update()
            
            is_dir = len(self.tree.get_children(child_id)) > 0
            
            # 子アイテムのパスを取得し正規化
            try:
                child_path = self.get_item_path(child_id)
                if not child_path:
                    continue
                
                child_path = os.path.normpath(child_path)
                
                if status == "exclude":
                    # 空のvaluesを設定
                    self.tree.item(child_id, values=())
                    self.excluded_items.add(child_id)
                    
                    # 設定に状態を保存
                    self.config_manager.set_excluded_item(self.current_dir, child_path, True)
                    
                    # アイコンを変更
                    if is_dir and self.locked_folder_icon:
                        self.tree.item(child_id, image=self.locked_folder_icon)
                    elif not is_dir and self.locked_file_icon:
                        self.tree.item(child_id, image=self.locked_file_icon)
                    else:
                        # アイコンが使えない場合はテキストを変更
                        text = self.tree.item(child_id, "text")
                        if "📁" in text:
                            self.tree.item(child_id, text=text.replace("📁", "🔒"))
                        elif "🐍" in text or "📄" in text:
                            self.tree.item(child_id, text=text.replace("🐍", "🔒").replace("📄", "🔒"))
                    
                    # セルの背景色を変更
                    self.tree.item(child_id, tags=('excluded',))
                else:
                    # 空のvaluesを設定
                    self.tree.item(child_id, values=())
                    
                    # 設定に状態を保存
                    self.config_manager.set_excluded_item(self.current_dir, child_path, False)
                    
                    # アイコンを戻す
                    if is_dir and self.folder_icon:
                        self.tree.item(child_id, image=self.folder_icon)
                    elif not is_dir and self.file_icon:
                        self.tree.item(child_id, image=self.file_icon)
                    else:
                        # アイコンが使えない場合はテキストを変更
                        text = self.tree.item(child_id, "text")
                        if "🔒" in text:
                            if is_dir:
                                self.tree.item(child_id, text=text.replace("🔒", "📁"))
                            else:
                                # ファイル拡張子を確認
                                file_ext = os.path.splitext(child_path)[1].lower()
                                if file_ext == '.py':
                                    self.tree.item(child_id, text=text.replace("🔒", "🐍"))
                                else:
                                    self.tree.item(child_id, text=text.replace("🔒", "📄"))
                    
                    # セルの背景色を元に戻す
                    self.tree.item(child_id, tags=())
                    
                    if child_id in self.excluded_items:
                        self.excluded_items.remove(child_id)
                
                # 10個ごとにUIを更新
                if i % 10 == 0:
                    self.tree.update()
                
                # 再帰的に子ノードを処理（深さ優先）
                if is_dir:
                    self._set_children_status_with_progress(child_id, status, progress_window, progress_label, progress_bar)
            
            except Exception as e:
                print(f"アイテム処理エラー: {str(e)} - スキップします")
                continue
        
        # 最終更新
        if progress_window and progress_window.winfo_exists():
            progress_bar["value"] = 100
            progress_label.config(text=f"処理完了 ({total_children}/{total_children})")
            progress_window.update()
    
    def load_directory(self, path):
        """ディレクトリ構造をツリービューに読み込む（エラーハンドリング強化）"""
        try:
            # 処理中フラグを設定
            self.is_processing = True
            
            # 現在のツリービューをクリア
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            self.current_dir = os.path.normpath(path)
            self.excluded_items.clear()
            
            # 選択されたファイルをリセット
            self.selected_file = None
            
            # 設定に保存
            self.config_manager.set_last_directory(path)
            
            # ディレクトリが大きすぎないか確認（ファイル数をカウント）
            total_items = 0
            large_directory = False
            max_items_to_display = 5000  # 一度に表示する最大項目数
            
            for root, dirs, files in os.walk(path):
                # スキップすべきフォルダ名を除外
                dirs[:] = [d for d in dirs if d not in self.skip_folders]
                
                # EXEファイルを含むフォルダをスキップする場合
                if self.skip_exe_folders:
                    has_exe = any(f.lower().endswith(tuple(self.skip_extensions)) for f in files)
                    if has_exe:
                        dirs[:] = []  # サブディレクトリを探索しない
                
                total_items += len(dirs) + len(files)
                if total_items > max_items_to_display:
                    large_directory = True
                    break
            
            # 大きなディレクトリの場合は警告
            if large_directory:
                confirm = messagebox.askyesno(
                    "警告", 
                    f"このディレクトリには{max_items_to_display}個以上の項目が含まれています。\n"
                    "全ての項目を読み込むと時間がかかったり、アプリケーションが応答しなくなる可能性があります。\n\n"
                    "続行しますか？\n"
                    "（「いいえ」を選択すると、最初の{max_items_to_display}個の項目のみが表示されます）"
                )
                limit_items = not confirm
            else:
                limit_items = False
            
            # プログレスバーウィンドウの表示
            if total_items > 100:
                progress_window = tk.Toplevel(self.parent)
                progress_window.title("ディレクトリを読み込み中")
                progress_window.geometry("300x100")
                progress_window.resizable(False, False)
                progress_window.transient(self.parent)
                
                progress_label = ttk.Label(progress_window, text="ディレクトリ構造を読み込み中...")
                progress_label.pack(pady=10)
                
                progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
                progress_bar.pack(fill="x", padx=20)
                progress_bar.start(10)
                
                # ウィンドウを画面中央に配置
                progress_window.update_idletasks()
                x = self.parent.winfo_rootx() + (self.parent.winfo_width() - progress_window.winfo_width()) // 2
                y = self.parent.winfo_rooty() + (self.parent.winfo_height() - progress_window.winfo_height()) // 2
                progress_window.geometry(f"+{x}+{y}")
                progress_window.update()
            else:
                progress_window = None
            
            # ルートディレクトリを追加
            if self.folder_icon:
                # 空のvaluesを設定
                root_item = self.tree.insert("", "end", text=f" {os.path.basename(path)}", 
                                values=(), image=self.folder_icon, open=True)
            else:
                # 空のvaluesを設定
                root_item = self.tree.insert("", "end", text=f"📁 {os.path.basename(path)}", 
                                values=(), open=True)
            
            # 再帰的にディレクトリ構造を構築（項目数制限あり）
            counters = {"items": 0, "limit": max_items_to_display if limit_items else None}
            try:
                self._load_directory_recursively(root_item, path, counters)
            except TooManyItemsException:
                if progress_window and progress_window.winfo_exists():
                    progress_label.config(text=f"表示制限に達しました: {max_items_to_display}項目")
                    progress_window.update()
            
            # プログレスウィンドウを閉じる
            if progress_window and progress_window.winfo_exists():
                progress_bar.stop()
                progress_window.destroy()
            
            # 表示制限に達した場合は通知
            if limit_items and counters["items"] >= max_items_to_display:
                messagebox.showinfo(
                    "情報", 
                    f"表示項目数が制限に達しました ({max_items_to_display}項目)。\n"
                    "全ての項目が表示されているわけではありません。"
                )
            
            # デバッグ出力
            print(f"ディレクトリを読み込みました: {self.current_dir}")
            print(f"項目数: {counters['items']}")
            print(f"除外アイテム設定: {self.config_manager.get_excluded_items(self.current_dir)}")
        
        except Exception as e:
            messagebox.showerror("エラー", f"ディレクトリの読み込み中にエラーが発生しました: {str(e)}")
            
            traceback.print_exc()
        
        finally:
            # 処理中フラグを解除
            self.is_processing = False
    
    def _load_directory_recursively(self, parent, path, counters):
        """再帰的にディレクトリ構造を読み込む（項目数制限付き、EXEフォルダスキップ）"""
        try:
            # 表示制限に達したかチェック
            if counters["limit"] is not None and counters["items"] >= counters["limit"]:
                raise TooManyItemsException("表示制限に達しました")
            
            # ディレクトリ内の項目をソート（ディレクトリ→ファイル）
            try:
                items = os.listdir(path)
            except PermissionError:
                # アクセス権限がない場合は空のvaluesを設定
                self.tree.item(parent, values=())
                return
            except Exception as e:
                # その他のエラー
                print(f"ディレクトリ読み込みエラー: {str(e)} - スキップします")
                return
            
            dirs = []
            files = []
            
            # EXEファイルを含むかどうかをチェック
            has_exe = False
            
            for item in items:
                item_path = os.path.join(path, item)
                try:
                    # フォルダ名に基づくスキップをチェック
                    basename = os.path.basename(item_path)
                    if os.path.isdir(item_path):
                        if basename in self.skip_folders:
                            continue
                        dirs.append(item)
                    else:
                        # EXEファイルのチェック
                        if any(item.lower().endswith(ext) for ext in self.skip_extensions):
                            has_exe = True
                        
                        files.append(item)
                except Exception as e:
                    print(f"項目チェックエラー: {str(e)} - スキップします")
                    continue
            
            # EXEファイルが含まれていて、スキップ設定がONの場合
            if has_exe and self.skip_exe_folders:
                # このディレクトリ自体は表示するが、中身は空のvaluesを設定
                self.tree.item(parent, values=())
                return
            
            # 設定から除外状態を取得
            excluded_items = self.config_manager.get_excluded_items(self.current_dir)
            
            # ディレクトリを追加
            for dir_name in sorted(dirs):
                # 表示制限に達したかチェック
                if counters["limit"] is not None and counters["items"] >= counters["limit"]:
                    raise TooManyItemsException("表示制限に達しました")
                
                counters["items"] += 1
                
                try:
                    dir_path = os.path.normpath(os.path.join(path, dir_name))
                    
                    # 設定から除外状態を取得 - 正規化されたパスを使用
                    is_excluded = excluded_items.get(dir_path, False)
                    
                    if self.folder_icon:
                        image = self.locked_folder_icon if is_excluded else self.folder_icon
                        # valuesにステータステキストを表示しない
                        dir_id = self.tree.insert(parent, "end", text=f" {dir_name}", 
                                             values=(), image=image, open=False)
                    else:
                        icon = "🔒" if is_excluded else "📁"
                        # valuesにステータステキストを表示しない
                        dir_id = self.tree.insert(parent, "end", text=f"{icon} {dir_name}", 
                                             values=(), open=False)
                    
                    if is_excluded:
                        self.excluded_items.add(dir_id)
                        self.tree.tag_configure('excluded', foreground='#999999')
                        self.tree.item(dir_id, tags=('excluded',))
                    
                    # 100個ごとにUIを更新
                    if counters["items"] % 100 == 0:
                        self.tree.update()
                    
                    # サブディレクトリを再帰的に処理
                    self._load_directory_recursively(dir_id, dir_path, counters)
                
                except TooManyItemsException:
                    # 再帰呼び出しで制限に達した場合は上位に伝播
                    raise
                except Exception as e:
                    print(f"ディレクトリ追加エラー: {str(e)} - スキップします")
                    continue
            
            # ファイルを追加（EXEファイルはスキップ）
            for file_name in sorted(files):
                # スキップすべき拡張子なら除外
                if any(file_name.lower().endswith(ext) for ext in self.skip_extensions):
                    continue
                
                # 表示制限に達したかチェック
                if counters["limit"] is not None and counters["items"] >= counters["limit"]:
                    raise TooManyItemsException("表示制限に達しました")
                
                counters["items"] += 1
                
                try:
                    file_path = os.path.normpath(os.path.join(path, file_name))
                    
                    # 設定から除外状態を取得 - 正規化されたパスを使用
                    is_excluded = excluded_items.get(file_path, False)
                    
                    # ファイルアイコンの選択（拡張子に基づく）
                    file_ext = os.path.splitext(file_name)[1].lower()
                    icon_text = "🐍" if file_ext == '.py' else "📄"  # Pythonファイルとそれ以外で分ける
                    
                    if self.file_icon:
                        image = self.locked_file_icon if is_excluded else self.file_icon
                        # valuesにステータステキストを表示しない
                        file_id = self.tree.insert(parent, "end", text=f" {file_name}", 
                                                values=(), image=image)
                    else:
                        icon = "🔒" if is_excluded else icon_text
                        # valuesにステータステキストを表示しない
                        file_id = self.tree.insert(parent, "end", text=f"{icon} {file_name}", 
                                                values=())
                    
                    if is_excluded:
                        self.excluded_items.add(file_id)
                        self.tree.tag_configure('excluded', foreground='#999999')
                        self.tree.item(file_id, tags=('excluded',))
                    
                    # 100個ごとにUIを更新
                    if counters["items"] % 100 == 0:
                        self.tree.update()
                
                except TooManyItemsException:
                    # 再帰呼び出しで制限に達した場合は上位に伝播
                    raise
                except Exception as e:
                    print(f"ファイル追加エラー: {str(e)} - スキップします")
                    continue
        
        except PermissionError:
            # アクセス権限がない場合は空のvaluesを設定
            self.tree.item(parent, values=())
        except TooManyItemsException:
            # 項目数制限に達した場合は上位に伝播
            raise
        except Exception as e:
            print(f"ディレクトリ処理エラー: {str(e)} - スキップします")
            
    # オプション設定のためのトグルメソッドを追加
    def toggle_skip_exe_folders(self):
        """EXEファイルを含むフォルダをスキップするかどうかを切り替える"""
        self.skip_exe_folders = not self.skip_exe_folders
        return self.skip_exe_folders
        
    def get_included_files(self, include_python_only=True):
        """解析対象のファイルパスリストを取得"""
        if not self.current_dir or not self.tree or not self.tree.winfo_exists():
            return []
        
        included_files = []
        
        def traverse_tree(node, parent_path):
            # 現在のノードが除外リストに含まれているかチェック
            if node in self.excluded_items:
                return
            
            item_text = self.tree.item(node, "text")
            # 先頭の絵文字やスペースを削除
            clean_text = item_text.strip()
            if clean_text.startswith("📁 ") or clean_text.startswith("🐍 ") or clean_text.startswith("🔒 ") or clean_text.startswith("📄 "):
                clean_text = clean_text[2:].strip()
            elif " " in clean_text and clean_text[0] != " ":
                clean_text = clean_text.split(" ", 1)[1].strip()
            
            current_path = os.path.join(parent_path, clean_text)
            
            # ファイルかディレクトリかを確認
            is_dir = len(self.tree.get_children(node)) > 0
            if not is_dir:
                # Pythonファイルのみを含める場合の条件
                if not include_python_only or clean_text.endswith('.py'):
                    included_files.append(current_path)
            
            # 子ノードを処理
            for child in self.tree.get_children(node):
                traverse_tree(child, current_path)
        
        # ルートディレクトリから全てのノードを処理
        root_node = self.tree.get_children()[0]
        # ルートディレクトリのテキストから絵文字とスペースを削除
        root_text = self.tree.item(root_node, "text").strip()
        if root_text.startswith("📁 ") or root_text.startswith("🔒 "):
            root_text = root_text[2:].strip()
        elif " " in root_text and root_text[0] != " ":
            root_text = root_text.split(" ", 1)[1].strip()
        
        parent_dir = os.path.dirname(self.current_dir)
        traverse_tree(root_node, parent_dir)
        
        return included_files
        
class TooManyItemsException(Exception):
    """表示する項目数の制限に達したことを示す例外"""
    pass

class SyntaxHighlighter:
    """
    Pythonコードに構文ハイライトを適用するクラス
    """
    def __init__(self, text_widget):
        self.text_widget = text_widget
        
        # 構文ハイライトの色定義
        self.colors = {
            'keywords': '#FF7700',  # オレンジ
            'builtins': '#0086B3',  # 水色
            'strings': '#008800',   # 緑
            'comments': '#888888',  # グレー
            'functions': '#0000FF', # 青
            'classes': '#990000',   # 赤
            'docstrings': '#067D17', # 深緑
        }
        
        # キーワードと組み込み関数の定義
        self.keywords = ['and', 'as', 'assert', 'break', 'class', 'continue', 'def', 
                   'del', 'elif', 'else', 'except', 'False', 'finally', 'for', 
                   'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 
                   'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True', 
                   'try', 'while', 'with', 'yield']
        
        self.builtins = ['abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 
                   'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex', 
                   'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 
                   'filter', 'float', 'format', 'frozenset', 'getattr', 'globals', 
                   'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 
                   'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 
                   'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 
                   'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 
                   'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip']
        
        # テキストウィジェットのタグを設定
        for tag, color in self.colors.items():
            self.text_widget.tag_configure(tag, foreground=color)
    
    def highlight(self, event=None):
        """テキストにシンタックスハイライトを適用"""
        # 現在のテキストをすべて取得
        content = self.text_widget.get("1.0", "end-1c")
        
        # すべてのタグをクリア
        for tag in self.colors.keys():
            self.text_widget.tag_remove(tag, "1.0", "end")
        
        # 構文ハイライトを適用
        self._apply_highlights(content)
    
    def _apply_highlights(self, content):
        """ハイライトを適用する内部メソッド"""
        # コメント（#から行末まで）
        for match in re.finditer(r'#.*$', content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('comments', start, end)
        
        # 文字列（三重引用符）
        for match in re.finditer(r'""".*?"""|\'\'\'.*?\'\'\'', content, re.DOTALL):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('docstrings', start, end)
        
        # 文字列（単一または二重引用符）
        for match in re.finditer(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('strings', start, end)
        
        # クラス定義とdef
        for match in re.finditer(r'\b(class|def)\s+(\w+)', content):
            keyword_start = f"1.0+{match.start(1)}c"
            keyword_end = f"1.0+{match.end(1)}c"
            self.text_widget.tag_add('keywords', keyword_start, keyword_end)
            
            if match.group(1) == 'class':
                name_start = f"1.0+{match.start(2)}c"
                name_end = f"1.0+{match.end(2)}c"
                self.text_widget.tag_add('classes', name_start, name_end)
            else:
                name_start = f"1.0+{match.start(2)}c"
                name_end = f"1.0+{match.end(2)}c"
                self.text_widget.tag_add('functions', name_start, name_end)
        
        # キーワード
        for keyword in self.keywords:
            for match in re.finditer(r'\b' + keyword + r'\b', content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text_widget.tag_add('keywords', start, end)
        
        # 組み込み関数
        for builtin in self.builtins:
            for match in re.finditer(r'\b' + builtin + r'\b', content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text_widget.tag_add('builtins', start, end)

class CodeAnalyzerApp:
    """
    コード解析ツールのGUIアプリケーション
    """
    def __init__(self, root):
        """アプリケーションの初期化"""
        self.root = root
        self.root.title("Pythonコード解析ツール")
        
        # 設定マネージャーを初期化
        self.config_manager = ConfigManager()

        # current_prompt_id変数を先に初期化する
        self.current_prompt_id = None
        
        # ウィンドウサイズを設定
        window_size = self.config_manager.get_window_size()
        window_width = window_size["width"]
        window_height = window_size["height"]
        self.root.geometry(f"{window_width}x{window_height}")
        
        self.analyzer = CodeAnalyzer()
        
        # AstroidAnalyzerの初期化
        self.astroid_analyzer = AstroidAnalyzer()
        
        # メインスタイルの設定
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TButton", font=('Helvetica', 10), padding=5)
        style.configure("TLabel", font=('Helvetica', 11), background="#f0f0f0")
        style.configure("Stats.TLabel", font=('Helvetica', 9), foreground="#666666")

        # プロンプト用のアクセントボタンスタイル
        style.configure("Accent.TButton", font=('Helvetica', 10, 'bold'))

        # スタイルマップの設定
        style.map("Treeview", foreground=[("disabled", "#a0a0a0")], 
                background=[("disabled", "#f0f0f0")])
        
        # ツリービューのカスタムスタイル
        style.configure("Treeview", 
                        background="#ffffff", 
                        foreground="#000000", 
                        rowheight=26,
                        fieldbackground="#ffffff")
        
        # 選択項目のハイライトスタイル - 選択状態をより明確に
        style.map("Treeview", 
                  background=[("selected", "#e0e0ff")],
                  foreground=[("selected", "#000000")])
        
        # ツリービューヘッダーのスタイル
        style.configure("Treeview.Heading", 
                        font=('Helvetica', 10, 'bold'),
                        background="#e0e0e0")
        
        # 含む/除外の視覚的なスタイル
        style.configure("Include.TLabel", foreground="green", font=('Helvetica', 10))
        style.configure("Exclude.TLabel", foreground="red", font=('Helvetica', 10))
        
        # メインフレーム
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(expand=True, fill="both")
        
        # ツールバーフレーム - シンプルな横並びに変更
        self.toolbar_frame = ttk.Frame(self.main_frame)
        self.toolbar_frame.pack(fill="x", pady=(0, 10))

        # ボタンを横に並べてコンパクトに配置
        self.import_dir_button = ttk.Button(self.toolbar_frame, text="📁 import", 
                                           command=self.import_directory)
        self.import_dir_button.pack(side="left", padx=5)

        # 解析ボタン
        self.analyze_button = ttk.Button(self.toolbar_frame, text="🔍 analysis", 
                                        command=self.analyze_selected)
        self.analyze_button.pack(side="left", padx=5)

        # コピーボタン
        self.copy_button = ttk.Button(self.toolbar_frame, text="📝 Copy", 
                                     command=self.copy_to_clipboard)
        self.copy_button.pack(side="left", padx=5)
        
        # JSONエクスポートボタン
        # self.export_json_button = ttk.Button(self.toolbar_frame, text="📊 JSON出力", 
                                             # command=self.export_to_json)
        # self.export_json_button.pack(side="left", padx=5)
        
        # ペイン分割（左右に分割）- 比率を30:70に
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(expand=True, fill="both")
        
        # 左側フレーム（ディレクトリツリー用）- 30%
        self.left_frame = ttk.Frame(self.paned_window, width=int(window_width * 0.3))
        self.left_frame.pack_propagate(False)  # サイズを固定
        self.paned_window.add(self.left_frame, weight=1)
        
        # 右側フレーム（結果表示用）- 70%
        self.right_frame = ttk.Frame(self.paned_window, width=int(window_width * 0.7))
        self.paned_window.add(self.right_frame, weight=4)
        
        # ディレクトリツリービュー - 設定マネージャーを渡す
        self.dir_tree_view = DirectoryTreeView(self.left_frame, self.config_manager)
        self.dir_tree_view.set_file_selected_callback(self.on_file_selected)
        self.dir_tree_view.set_dir_selected_callback(self.on_dir_selected)

        # タブコントロールの作成（packはまだしない）
        self.tab_control = ttk.Notebook(self.right_frame)

        # タブ選択パネルの作成
        self.tab_selection_panel = self.create_tab_selection_panel()
        self.tab_selection_panel.pack(fill="x", pady=(0, 5))

        # 解析結果タブの作成
        self.result_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.result_tab, text=" 解析結果 ")

        # 拡張解析タブの作成
        self.extended_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.extended_tab, text=" 拡張解析 ")
        
        # JSONタブの作成
        self.json_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.json_tab, text=" JSON出力 ")

        # JSONテキストエリアのラベル
        self.json_label = ttk.Label(self.json_tab, text="JSON形式のコード構造:")
        self.json_label.pack(anchor="w", pady=(0, 5))

        # JSONテキストエリア
        self.json_text = scrolledtext.ScrolledText(self.json_tab, font=('Consolas', 10))
        self.json_text.pack(expand=True, fill="both")

        # JSONテキストにもシンタックスハイライターを適用
        self.json_highlighter = SyntaxHighlighter(self.json_text)
        
        # プロンプト入力タブの作成
        self.prompt_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.prompt_tab, text=" プロンプト入力 ")

        # タブコントロールを後からpack
        self.tab_control.pack(expand=True, fill="both")

        # タブ切り替えイベントをバインド
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # 結果テキストエリアのラベル
        self.result_label = ttk.Label(self.result_tab, text="解析結果:")
        self.result_label.pack(anchor="w", pady=(0, 5))

        # 結果テキストエリア - result_tabに配置
        self.result_text = scrolledtext.ScrolledText(self.result_tab, font=('Consolas', 10))
        self.result_text.pack(expand=True, fill="both")
        
        # 拡張解析テキストエリアのラベル
        self.extended_label = ttk.Label(self.extended_tab, text="astroidによる拡張解析結果:")
        self.extended_label.pack(anchor="w", pady=(0, 5))

        # 拡張解析テキストエリア
        self.extended_text = scrolledtext.ScrolledText(self.extended_tab, font=('Consolas', 10))
        self.extended_text.pack(expand=True, fill="both")

        # プロンプトマネージャーの初期化
        self.prompt_manager = PromptManager(self.config_manager)
        
        # プロンプト関連のUI変数の初期化
        self.prompt_modified = False  # 変更フラグ
        
        # プロンプト入力タブのUIをセットアップ
        self.setup_prompt_tab()

        # 結果テキストエリアにシンタックスハイライターを適用
        self.result_highlighter = SyntaxHighlighter(self.result_text)
        
        # 拡張解析テキストエリアにもハイライターを適用
        self.extended_highlighter = SyntaxHighlighter(self.extended_text)
                    
        # ステータスバー
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill="x", pady=(5, 0))

        # 左側ステータス（現在のファイル情報）
        self.file_status = ttk.Label(self.status_frame, text="準備完了", style="Stats.TLabel")
        self.file_status.pack(side="left")

        # 右側ステータス（文字数表示）
        self.char_count_label = ttk.Label(self.status_frame, text="文字数: 0", style="Stats.TLabel")
        self.char_count_label.pack(side="right")

        # 表示オプションフレーム - ログフィールドの下に配置
        self.option_frame = ttk.Frame(self.status_frame)
        self.option_frame.pack(side="right", padx=20)

        # インポート文を含めるかどうかのチェックボックス変数
        self.show_imports = tk.BooleanVar(value=True)
        # docstringを表示するかどうかのチェックボックス変数
        self.show_docstrings = tk.BooleanVar(value=True)
        # EXEを含むフォルダをスキップするかどうかのチェックボックス変数
        self.skip_exe_folders = tk.BooleanVar(value=True)

        # オプションラベル
        option_label = ttk.Label(self.option_frame, text="表示オプション:", style="Stats.TLabel")
        option_label.pack(side="left", padx=5)

        # インポート文を表示するチェックボックス
        self.imports_check = ttk.Checkbutton(
            self.option_frame, 
            text="インポート文", 
            variable=self.show_imports,
            command=self.toggle_display_options
        )
        self.imports_check.pack(side="left", padx=5)

        # docstringを表示するチェックボックス
        self.docstrings_check = ttk.Checkbutton(
            self.option_frame, 
            text="説明文", 
            variable=self.show_docstrings,
            command=self.toggle_display_options
        )
        self.docstrings_check.pack(side="left", padx=5)

        # EXEを含むフォルダをスキップするチェックボックス
        self.exe_skip_check = ttk.Checkbutton(
            self.option_frame, 
            text="EXEフォルダスキップ", 
            variable=self.skip_exe_folders,
            command=self.toggle_exe_folder_skip
        )
        self.exe_skip_check.pack(side="left", padx=5)

        # 現在のディレクトリパス
        self.current_dir = None
        
        # 選択されたファイル
        self.selected_file = None
        
        # テキストエディタのショートカットとコンテキストメニューを設定
        self.setup_text_editor_shortcuts()
        
        # ウィンドウを中央に配置
        self.center_window()
        
        # ウィンドウのリサイズイベントをバインド
        self.root.bind("<Configure>", self.on_window_resize)
        
        # ウィンドウが閉じられる前のイベントをバインド
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 拡張解析テキストエリアにもショートカットを設定
        self.setup_editor_shortcuts(self.extended_text)

        # 前回のディレクトリまたはファイルを読み込む
        self.load_last_session()


    def setup_prompt_tab(self):
        """プロンプト入力タブのUIを構築する"""
        # プロンプトマネージャーの初期化
        self.prompt_manager = PromptManager(self.config_manager)

        # プロンプトタブを左右に分割
        self.prompt_paned = ttk.PanedWindow(self.prompt_tab, orient=tk.HORIZONTAL)
        self.prompt_paned.pack(expand=True, fill="both")

        # 左側フレーム（プロンプト一覧）を設定
        self.setup_prompt_list_frame()
        
        # 右側フレーム（プロンプト編集）を設定
        self.setup_prompt_edit_frame()
        
        # 下部のボタンエリアを設定
        self.setup_prompt_button_frame()
        
        # プロンプト一覧を更新
        self.update_prompt_list()

        # 最初のプロンプトを選択
        if self.prompt_tree.get_children():
            self.current_prompt_id = self.prompt_tree.get_children()[0]
            self.prompt_tree.selection_set(self.current_prompt_id)
            self.prompt_tree.focus(self.current_prompt_id)
            self.on_prompt_selected(None)

        # ショートカットの設定
        self.bind_prompt_shortcuts()

    def setup_prompt_context_menu(self):
        """プロンプト一覧の右クリックメニューを設定"""
        self.prompt_context_menu = tk.Menu(self.prompt_tree, tearoff=0)
        self.prompt_context_menu.add_command(label="新規作成", command=self.create_new_prompt)
        self.prompt_context_menu.add_command(label="複製", command=self.duplicate_current_prompt)
        self.prompt_context_menu.add_command(label="削除", command=self.delete_current_prompt)
        
        # 右クリックイベントをバインド
        if sys.platform == 'darwin':  # macOS
            self.prompt_tree.bind("<Button-2>", self.show_prompt_context_menu)
        else:  # Windows/Linux
            self.prompt_tree.bind("<Button-3>", self.show_prompt_context_menu)

    def show_prompt_context_menu(self, event):
        """プロンプト一覧の右クリックメニューを表示"""
        try:
            # クリックした位置の項目を特定
            item = self.prompt_tree.identify_row(event.y)
            if item:
                # 項目を選択
                self.prompt_tree.selection_set(item)
                self.prompt_tree.focus(item)
                self.on_prompt_selected(None)
                
                # メニューを表示
                self.prompt_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.prompt_context_menu.grab_release()

    def setup_prompt_list_frame(self):
        """プロンプト一覧フレームを設定"""
        # 左側フレーム
        self.prompt_list_frame = ttk.Frame(self.prompt_paned, width=220)
        self.prompt_paned.add(self.prompt_list_frame, weight=1)
        
        # 一覧上部のヘッダーフレーム
        list_header_frame = ttk.Frame(self.prompt_list_frame)
        list_header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        # 「プロンプト一覧」ラベル
        list_label = ttk.Label(list_header_frame, text="プロンプト一覧", font=('Helvetica', 10, 'bold'))
        list_label.pack(side="left", padx=5)
        
        # プロンプト操作ボタン（+と-）をヘッダーの右側に配置
        button_frame = ttk.Frame(list_header_frame)
        button_frame.pack(side="right", padx=2)
        
        # コンパクトなボタン用のスタイル設定
        style = ttk.Style()
        style.configure("Compact.TButton", 
                       padding=0,       # パディングを0に設定
                       font=('Helvetica', 8),  # フォントサイズ縮小
                       width=1)         # 幅を最小限に設定
        
        # 新規作成ボタン（+）- コンパクトスタイル適用
        self.add_prompt_btn = ttk.Button(button_frame, text="+", style="Compact.TButton",
                                       command=self.create_new_prompt)
        self.add_prompt_btn.pack(side="left", padx=1)
        self.add_tooltip(self.add_prompt_btn, "新規プロンプト作成")
        
        # 削除ボタン（-）- コンパクトスタイル適用
        self.remove_prompt_btn = ttk.Button(button_frame, text="-", style="Compact.TButton",
                                          command=self.delete_current_prompt)
        self.remove_prompt_btn.pack(side="left", padx=1)
        self.add_tooltip(self.remove_prompt_btn, "選択したプロンプトを削除")
        
        # 区切り線
        separator = ttk.Separator(self.prompt_list_frame, orient="horizontal")
        separator.pack(fill="x", padx=5, pady=5)
        
        # プロンプト一覧（ツリービュー）
        self.prompt_tree = ttk.Treeview(self.prompt_list_frame, columns=("name",), show="headings", height=15)
        self.prompt_tree.heading("name", text="プロンプト名")
        self.prompt_tree.column("name", width=200, anchor="w")
        
        # スクロールバー - より細く設定
        tree_scroll = ttk.Scrollbar(self.prompt_list_frame, orient="vertical", command=self.prompt_tree.yview)
        self.prompt_tree.configure(yscrollcommand=tree_scroll.set)
        
        # ツリービューとスクロールバーを配置 - スクロールバーを右端に完全に寄せる
        self.prompt_tree.pack(side="left", expand=True, fill="both", padx=(5, 0), pady=5)
        tree_scroll.pack(side="right", fill="y", pady=5)
        
        # プロンプトツリーの選択イベント
        self.prompt_tree.bind("<<TreeviewSelect>>", self.on_prompt_selected)
        
        # 右クリックメニューの追加
        self.setup_prompt_context_menu()

    def setup_prompt_context_menu(self):
        """プロンプト一覧の右クリックメニューを設定"""
        self.prompt_context_menu = tk.Menu(self.prompt_tree, tearoff=0)
        self.prompt_context_menu.add_command(label="新規作成", command=self.create_new_prompt)
        self.prompt_context_menu.add_command(label="複製", command=self.duplicate_current_prompt)
        self.prompt_context_menu.add_command(label="削除", command=self.delete_current_prompt)
        
        # 右クリックイベントをバインド
        if sys.platform == 'darwin':  # macOS
            self.prompt_tree.bind("<Button-2>", self.show_prompt_context_menu)
        else:  # Windows/Linux
            self.prompt_tree.bind("<Button-3>", self.show_prompt_context_menu)

    def show_prompt_context_menu(self, event):
        """プロンプト一覧の右クリックメニューを表示"""
        try:
            # クリックした位置の項目を特定
            item = self.prompt_tree.identify_row(event.y)
            if item:
                # 項目を選択
                self.prompt_tree.selection_set(item)
                self.prompt_tree.focus(item)
                self.on_prompt_selected(None)
                
                # メニューを表示
                self.prompt_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.prompt_context_menu.grab_release()

    def setup_prompt_edit_frame(self):
        """プロンプト編集フレームを設定"""
        # 右側フレーム
        self.prompt_edit_frame = ttk.Frame(self.prompt_paned)
        self.prompt_paned.add(self.prompt_edit_frame, weight=3)
        
        # プロンプト名入力エリア
        name_frame = ttk.Frame(self.prompt_edit_frame)
        name_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.prompt_name_label = ttk.Label(name_frame, text="プロンプト名:", font=('Helvetica', 10))
        self.prompt_name_label.pack(side="left", padx=(0, 5))
        
        self.prompt_name_var = tk.StringVar()
        self.prompt_name_entry = ttk.Entry(name_frame, textvariable=self.prompt_name_var, font=('Helvetica', 10))
        self.prompt_name_entry.pack(side="left", fill="x", expand=True)
        
        # 区切り線
        separator = ttk.Separator(self.prompt_edit_frame, orient="horizontal")
        separator.pack(fill="x", padx=10, pady=5)
        
        # エディタラベル
        editor_label_frame = ttk.Frame(self.prompt_edit_frame)
        editor_label_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        editor_label = ttk.Label(editor_label_frame, text="プロンプト内容:", font=('Helvetica', 10))
        editor_label.pack(side="left")
        
        # 編集ステータス
        self.edit_status_var = tk.StringVar(value="未変更")
        self.edit_status_label = ttk.Label(editor_label_frame, textvariable=self.edit_status_var,
                                         font=('Helvetica', 9), foreground="#999999")
        self.edit_status_label.pack(side="right")
        
        # プロンプト編集エリア（エディタ）
        self.prompt_text = scrolledtext.ScrolledText(
            self.prompt_edit_frame, 
            font=('Consolas', 10),
            wrap=tk.WORD,
            undo=True
        )
        self.prompt_text.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        
        # テキスト変更時のイベント設定
        self.prompt_text.bind("<<Modified>>", self.on_prompt_text_modified)

    def setup_prompt_button_frame(self):
        """プロンプト操作ボタンフレームの設定"""
        # ボタンエリア（ステータスバー的なフレーム）
        self.prompt_button_frame = ttk.Frame(self.prompt_tab)
        self.prompt_button_frame.pack(fill="x", side="bottom", padx=0, pady=0)
        
        # 区切り線
        separator = ttk.Separator(self.prompt_button_frame, orient="horizontal")
        separator.pack(fill="x")
        
        # ボタン配置用の内部フレーム
        button_container = ttk.Frame(self.prompt_button_frame)
        button_container.pack(fill="x", padx=10, pady=8)
        
        # 新規ボタン
        self.new_prompt_button = ttk.Button(
            button_container, 
            text="新規作成", 
            command=self.create_new_prompt,
            style="Accent.TButton"
        )
        self.new_prompt_button.pack(side="left", padx=(0, 5))
        
        # 名前を付けて保存ボタン
        self.save_as_prompt_button = ttk.Button(
            button_container, 
            text="名前を付けて保存", 
            command=self.save_prompt_as
        )
        self.save_as_prompt_button.pack(side="left", padx=5)
        
        # 保存ボタン
        self.save_prompt_button = ttk.Button(
            button_container, 
            text="保存 (Ctrl+S)", 
            command=self.save_current_prompt
        )
        self.save_prompt_button.pack(side="left", padx=5)
        
        # 削除ボタン - 右端に配置
        self.delete_prompt_button = ttk.Button(
            button_container, 
            text="削除", 
            command=self.delete_current_prompt
        )
        self.delete_prompt_button.pack(side="right")
        
        # 文字数カウンタ
        self.prompt_char_count_var = tk.StringVar(value="文字数: 0")
        char_count_label = ttk.Label(
            button_container, 
            textvariable=self.prompt_char_count_var,
            font=('Helvetica', 9),
            foreground="#666666"
        )
        char_count_label.pack(side="right", padx=10)

    def bind_prompt_shortcuts(self):
        """プロンプト編集関連のショートカットキーをバインド"""
        # Ctrl+S で保存
        self.prompt_text.bind("<Control-s>", lambda event: self.save_current_prompt())
        # Ctrl+N で新規作成
        self.prompt_text.bind("<Control-n>", lambda event: self.create_new_prompt())
        # Ctrl+Shift+S で名前を付けて保存
        self.prompt_text.bind("<Control-Shift-S>", lambda event: self.save_prompt_as())
        # エスケープキーでフォーカスをプロンプトリストに移動
        self.prompt_text.bind("<Escape>", lambda event: self.prompt_tree.focus_set())

    def add_tooltip(self, widget, text):
        """ウィジェットにツールチップを追加"""
        # シンプルなツールチップ実装
        def enter(event):
            if not hasattr(self, 'tooltip'):
                self.tooltip = tk.Toplevel(widget)
                self.tooltip.wm_overrideredirect(True)
                self.tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")
                label = ttk.Label(self.tooltip, text=text, background="#FFFFCC", 
                                 relief="solid", borderwidth=1, padding=2)
                label.pack()
        
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                del self.tooltip
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def on_prompt_selected(self, event):
        """プロンプトが選択されたときの処理"""
        selected_items = self.prompt_tree.selection()
        if not selected_items:
            return
        
        # 未保存の変更があれば確認
        if hasattr(self, 'prompt_modified') and self.prompt_modified:
            if not messagebox.askyesno("確認", "現在のプロンプトに未保存の変更があります。\n変更を破棄しますか？"):
                # 選択を元に戻す（現在の選択を維持）
                if self.current_prompt_id:
                    self.prompt_tree.selection_set(self.current_prompt_id)
                return
        
        prompt_id = selected_items[0]
        self.current_prompt_id = prompt_id
        
        # プロンプト名と内容を表示
        prompt_name = self.prompt_manager.get_prompt_name(prompt_id)
        prompt_content = self.prompt_manager.get_prompt(prompt_id)
        
        self.prompt_name_var.set(prompt_name)
        
        # テキスト変更イベントが発生しないように一時的にバインドを解除
        self.prompt_text.bind("<<Modified>>", lambda e: None)
        
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(tk.END, prompt_content)
        
        # 変更フラグをリセット
        self.prompt_modified = False
        self.edit_status_var.set("未変更")
        
        # テキスト変更イベントを再バインド
        self.prompt_text.bind("<<Modified>>", self.on_prompt_text_modified)
        self.prompt_text.edit_modified(False)  # 変更フラグをリセット
        
        # 文字数を更新
        char_count = len(prompt_content)
        self.prompt_char_count_var.set(f"文字数: {char_count}")
        
        # 現在表示されているタブがプロンプト入力タブであれば文字数ラベルも更新
        current_tab_index = self.tab_control.index(self.tab_control.select())
        if current_tab_index == 3:  # プロンプト入力タブ（インデックスが3）
            self.char_count_label.config(text=f"文字数: {char_count}")

    def on_prompt_text_modified(self, event):
        """プロンプトテキストが変更されたときの処理"""
        # Modifiedフラグがセットされている場合のみ処理
        if self.prompt_text.edit_modified():
            # テキスト内容を取得して文字数をカウント
            text_content = self.prompt_text.get(1.0, tk.END)
            char_count = len(text_content) - 1  # 最後の改行文字を除く
            
            # 文字数表示を更新
            self.prompt_char_count_var.set(f"文字数: {char_count}")
            
            # 変更フラグを設定
            self.prompt_modified = True
            self.edit_status_var.set("変更あり*")
            
            # Modifiedフラグをリセット（次の変更を検知するため）
            self.prompt_text.edit_modified(False)

    def create_new_prompt(self):
        """新規プロンプトを作成"""
        # 未保存の変更があれば確認
        if hasattr(self, 'prompt_modified') and self.prompt_modified:
            if not messagebox.askyesno("確認", "現在のプロンプトに未保存の変更があります。\n変更を破棄しますか？"):
                return
        
        # デフォルトの新規プロンプトテンプレート
        template = """# [ファイル/ディレクトリ名]の解析プロンプト

    以下のコード構造を分析して：
    [解析結果]

    ## 質問/指示
    [ここに質問や指示を入力してください]

    ## 特記事項
    [特記事項があれば記入してください]
    """
        
        # 新しいプロンプトIDを取得
        prompt_id = self.prompt_manager.add_prompt("新規プロンプト", template)
        
        # プロンプト一覧を更新して新しいプロンプトを選択
        self.update_prompt_list()
        self.prompt_tree.selection_set(prompt_id)
        self.prompt_tree.focus(prompt_id)
        self.prompt_tree.see(prompt_id)  # 選択項目が見えるようにスクロール
        self.on_prompt_selected(None)
        
        # 名前入力フィールドにフォーカス
        self.prompt_name_entry.focus_set()
        self.prompt_name_entry.select_range(0, tk.END)

    def duplicate_current_prompt(self):
        """現在のプロンプトを複製"""
        if not self.current_prompt_id:
            return
        
        # 現在のプロンプトの名前と内容を取得
        current_name = self.prompt_name_var.get()
        current_content = self.prompt_text.get(1.0, tk.END).strip()
        
        # 複製名を生成
        copy_name = f"{current_name} のコピー"
        
        # 新しいプロンプトを追加
        new_id = self.prompt_manager.add_prompt(copy_name, current_content)
        
        # プロンプト一覧を更新して新しいプロンプトを選択
        self.update_prompt_list()
        self.prompt_tree.selection_set(new_id)
        self.prompt_tree.focus(new_id)
        self.prompt_tree.see(new_id)
        self.on_prompt_selected(None)
        
        # 名前入力フィールドにフォーカス
        self.prompt_name_entry.focus_set()
        self.prompt_name_entry.select_range(0, tk.END)

    def save_current_prompt(self, event=None):
        """現在のプロンプトを保存"""
        if not self.current_prompt_id:
            return
        
        prompt_name = self.prompt_name_var.get().strip()
        prompt_content = self.prompt_text.get(1.0, tk.END).strip()
        
        if not prompt_name:
            messagebox.showwarning("警告", "プロンプト名を入力してください。")
            self.prompt_name_entry.focus_set()
            return
        
        if self.prompt_manager.update_prompt(self.current_prompt_id, name=prompt_name, content=prompt_content):
            # 保存成功
            self.update_prompt_list()
            
            # 変更フラグをリセット
            self.prompt_modified = False
            self.edit_status_var.set("保存済み")
            
            # 一定時間後に「未変更」に戻す
            self.root.after(2000, lambda: self.edit_status_var.set("未変更"))
            
            # ツリービュー内の選択項目を保存済みの名前で表示
            item_index = self.prompt_tree.index(self.current_prompt_id)
            self.prompt_tree.item(self.current_prompt_id, values=(prompt_name,))
            
            return True
        else:
            messagebox.showerror("エラー", "プロンプトの保存に失敗しました。")
            return False

    def save_prompt_as(self, event=None):
        """名前を付けて保存"""
        prompt_name = self.prompt_name_var.get().strip()
        prompt_content = self.prompt_text.get(1.0, tk.END).strip()
        
        # 名前入力ダイアログ
        new_name = simpledialog.askstring(
            "名前を付けて保存", 
            "新しいプロンプト名を入力してください:",
            initialvalue=f"{prompt_name} のコピー" if prompt_name else "新規プロンプト"
        )
        
        if not new_name:
            return False  # キャンセルされた
        
        # 新しいプロンプトとして保存
        new_id = self.prompt_manager.add_prompt(new_name, prompt_content)
        
        # プロンプト一覧を更新して新しいプロンプトを選択
        self.update_prompt_list()
        self.prompt_tree.selection_set(new_id)
        self.prompt_tree.focus(new_id)
        self.prompt_tree.see(new_id)
        self.on_prompt_selected(None)
        
        return True

    def delete_current_prompt(self):
        """選択されているプロンプトを削除"""
        if not self.current_prompt_id:
            return
        
        prompt_name = self.prompt_manager.get_prompt_name(self.current_prompt_id)
        
        # 確認ダイアログにプロンプト名を表示
        if messagebox.askyesno("確認", f"プロンプト '{prompt_name}' を削除しますか？\nこの操作は元に戻せません。"):
            if self.prompt_manager.delete_prompt(self.current_prompt_id):
                # 削除成功
                all_prompts = self.prompt_manager.get_all_prompts()
                if all_prompts:
                    # 他のプロンプトがある場合は最初のプロンプトを選択
                    self.current_prompt_id = next(iter(all_prompts))
                else:
                    # 全てのプロンプトが削除された場合はデフォルトプロンプトを作成
                    self.prompt_manager.create_default_prompt()
                    self.current_prompt_id = next(iter(self.prompt_manager.get_all_prompts()))
                
                self.update_prompt_list()
                self.prompt_tree.selection_set(self.current_prompt_id)
                self.prompt_tree.focus(self.current_prompt_id)
                self.on_prompt_selected(None)
            else:
                messagebox.showinfo("情報", "最後のプロンプトは削除できません。")

    def update_prompt_list(self):
        """プロンプト一覧を更新"""
        # ツリービューをクリア
        for item in self.prompt_tree.get_children():
            self.prompt_tree.delete(item)
        
        # プロンプト一覧を追加
        for prompt_id, prompt in self.prompt_manager.get_all_prompts().items():
            self.prompt_tree.insert("", "end", iid=prompt_id, text="", values=(prompt["name"],))
        
        # 現在のプロンプトIDが設定されていて、そのプロンプトが存在する場合に選択
        if hasattr(self, 'current_prompt_id') and self.current_prompt_id:
            if self.current_prompt_id in self.prompt_manager.get_all_prompts():
                self.prompt_tree.selection_set(self.current_prompt_id)
                self.prompt_tree.focus(self.current_prompt_id)
                self.prompt_tree.see(self.current_prompt_id)  # 選択項目が見えるようにスクロール

    def save_current_prompt_without_confirm(self):
        """現在のプロンプトを確認なしで保存（終了時などに使用）"""
        if hasattr(self, 'prompt_modified') and self.prompt_modified and self.current_prompt_id:
            prompt_name = self.prompt_name_var.get().strip()
            prompt_content = self.prompt_text.get(1.0, tk.END).strip()
            
            if not prompt_name:
                prompt_name = "無題のプロンプト"
            
            self.prompt_manager.update_prompt(self.current_prompt_id, name=prompt_name, content=prompt_content)

    def text_to_json_structure(self, text_content):
        """テキスト形式の解析結果をJSON構造に変換する"""
       
        result = {
            "directory_structure": [],
            "classes": [],
            "functions": [],
            "imports": []
        }
        
        current_section = None
        current_class = None
        current_function = None
        
        # 行ごとに解析
        for line in text_content.split('\n'):
            line = line.rstrip()
            
            # 空行はスキップ
            if not line:
                continue
                
            # セクションヘッダーの検出
            if line.startswith('# '):
                section_name = line[2:].lower()
                if 'ディレクトリ' in section_name:
                    current_section = 'directory'
                elif 'クラス' in section_name:
                    current_section = 'classes'
                elif '関数' in section_name:
                    current_section = 'functions'
                elif 'インポート' in section_name:
                    current_section = 'imports'
                else:
                    current_section = None
                continue
                
            # 現在のセクションに応じて処理
            if current_section == 'directory':
                if not line.startswith('#'):  # ヘッダー以外の行を追加
                    result["directory_structure"].append(line)
                    
            elif current_section == 'imports':
                result["imports"].append(line)
                
            elif current_section == 'classes':
                if line.startswith('class '):
                    # 新しいクラス定義
                    class_info = {"name": "", "file": "", "extends": "", "methods": []}
                    
                    # クラス名とファイル名を抽出（例: RecognizedText (voice2025.py)）
                    class_match = re.match(r'class\s+(\w+)(?:\s+<-\s+(\w+))?\s*(?:\((.*?)\))?', line)
                    if class_match:
                        class_info["name"] = class_match.group(1)
                        if class_match.group(2):  # 継承元がある場合
                            class_info["extends"] = class_match.group(2)
                        if class_match.group(3):  # ファイル名がある場合
                            class_info["file"] = class_match.group(3)
                    
                    current_class = class_info
                    result["classes"].append(current_class)
                    
                elif line.strip().startswith('メソッド:'):
                    # メソッドリストの開始
                    continue
                    
                elif line.strip().startswith('def ') and current_class:
                    # メソッド定義（クラス内のメソッド）
                    method_match = re.match(r'\s*def\s+([^(]+)', line)
                    if method_match:
                        method_name = method_match.group(1).strip()
                        current_class["methods"].append(method_name)
                        
                elif line.strip() and current_class and line.strip()[0].isspace():
                    # クラス配下のインデントされた行（メソッド定義の可能性）
                    method_match = re.match(r'\s+([^(]+)\(.*\)', line)
                    if method_match:
                        method_name = method_match.group(1).strip()
                        if method_name not in current_class["methods"]:
                            current_class["methods"].append(method_name)
                    
            elif current_section == 'functions':
                function_match = re.match(r'(?:def\s+)?([^(]+)(?:\(.*\))?(?:\s+->\s+.*)?', line)
                if function_match:
                    func_name = function_match.group(1).strip()
                    if func_name and not func_name.startswith('#'):
                        if func_name not in result["functions"]:
                            result["functions"].append(func_name)
        
        return result

    def extract_llm_structured_data(self, text):
        """拡張解析テキストからLLM向け構造化データを抽出する"""
        result = {
            "call_graph": {"data": []},
            "dependencies": {}
        }
        
        # LLM向け構造化データセクションを探す
        start_marker = "## LLM向け構造化データ"
        code_start = "```"
        code_end = "```"
        
        if start_marker in text:
            # セクション開始位置を見つける
            start_pos = text.find(start_marker)
            # コードブロック開始位置を見つける
            code_start_pos = text.find(code_start, start_pos)
            if code_start_pos != -1:
                # コードブロック終了位置を見つける
                code_end_pos = text.find(code_end, code_start_pos + len(code_start))
                if code_end_pos != -1:
                    # コードブロック内のテキストを抽出
                    code_content = text[code_start_pos + len(code_start):code_end_pos].strip()
                    
                    # コード内容を解析して構造化
                    current_section = None
                    current_subsection = None
                    
                    # コールグラフとデータセクションを格納する変数
                    call_graph_data = []
                    dependency_data = {}
                    current_dependency = None
                    
                    for line in code_content.split("\n"):
                        if line.startswith("# "):
                            # 新しいメインセクションの開始
                            current_section = line[2:].strip()
                            current_subsection = None
                            current_dependency = None
                            
                        elif current_section == "コールグラフ":
                            # コールグラフの行を追加
                            if line.strip() and " -> " in line:
                                call_graph_data.append(line.strip())
                                
                        elif current_section == "主要な関数依存関係":
                            # 関数依存関係の処理
                            if " -> " in line:
                                # 新しい依存関係の開始
                                parts = line.split(" -> ")
                                if len(parts) == 2:
                                    current_dependency = parts[0].strip()
                                    deps = [dep.strip() for dep in parts[1].split(",")]
                                    dependency_data[current_dependency] = deps
                            elif current_dependency and line.strip():
                                # 既存の依存関係の継続
                                deps = [dep.strip() for dep in line.split(",")]
                                if current_dependency in dependency_data:
                                    dependency_data[current_dependency].extend(deps)
                                else:
                                    dependency_data[current_dependency] = deps
                    
                    # 結果をまとめる
                    if call_graph_data:
                        result["call_graph"]["data"] = call_graph_data
                    if dependency_data:
                        result["dependencies"] = dependency_data
        
        return result


    def generate_call_graph(self, python_files):
        """指定されたPythonファイルからコールグラフを生成する"""
        try:
            if not python_files:
                return "コールグラフ生成対象のPythonファイルがありません。"
            
            # 関数/メソッドの呼び出し関係を保存する辞書
            call_graph = {}
            
            # 全てのモジュールをパースして保存
            modules = {}
            module_functions = {}  # モジュール内の関数とメソッドを記録
            
            # Step 1: すべてのモジュールをパースし、関数とメソッドを登録
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        code = file.read()
                    
                    module = astroid.parse(code)
                    module_name = os.path.basename(file_path).replace('.py', '')
                    modules[module_name] = module
                    
                    # このモジュール内の関数とメソッドを記録
                    module_functions[module_name] = {}
                    
                    # 関数の登録
                    for node in module.body:
                        if isinstance(node, astroid.FunctionDef):
                            full_name = f"{module_name}.{node.name}"
                            module_functions[module_name][node.name] = full_name
                            call_graph[full_name] = set()
                    
                    # クラスとそのメソッドの登録
                    for node in module.body:
                        if isinstance(node, astroid.ClassDef):
                            class_name = node.name
                            for method in node.body:
                                if isinstance(method, astroid.FunctionDef):
                                    full_name = f"{module_name}.{class_name}.{method.name}"
                                    module_functions[module_name][f"{class_name}.{method.name}"] = full_name
                                    call_graph[full_name] = set()
                
                except Exception as e:
                    print(f"ファイル {file_path} のパース中にエラー: {e}")
            
            # Step 2: 各モジュールを再度走査して呼び出し関係を構築
            for module_name, module in modules.items():
                self._analyze_module_calls(module, module_name, modules, module_functions, call_graph)
            
            # Step 3: コールグラフをテキスト形式で整形
            result = "# コールグラフ\n"
            
            # 呼び出し元がある関数のみを表示（外部から呼ばれないユーティリティ関数を除外）
            has_callers = set()
            for callee_set in call_graph.values():
                has_callers.update(callee_set)
            
            # 呼び出し元から呼び出し先を整理
            sorted_callers = sorted(call_graph.keys())
            for caller in sorted_callers:
                if caller in has_callers or call_graph[caller]:  # 呼び出される関数か、他の関数を呼び出す関数
                    callees = sorted(call_graph[caller])
                    if callees:
                        result += f"{caller} -> {', '.join(callees)}\n"
            
            return result
        
        except ImportError:
            return "astroidライブラリがインストールされていません。\npip install astroid でインストールしてください。"
        except Exception as e:
            
            traceback.print_exc()
            return f"コールグラフの生成中にエラーが発生しました:\n{str(e)}"

    def _analyze_module_calls(self, module, module_name, modules, module_functions, call_graph):
        """モジュール内の関数呼び出しを解析する"""
        
        def find_calls_in_node(node, caller_name):
            """ノード内の関数呼び出しを再帰的に検索"""
            if isinstance(node, astroid.Call):
                # 直接の関数呼び出し
                if isinstance(node.func, astroid.Name):
                    called_name = node.func.name
                    # 同一モジュール内の関数呼び出し
                    if called_name in module_functions.get(module_name, {}):
                        full_called_name = module_functions[module_name][called_name]
                        call_graph[caller_name].add(full_called_name)
                
                # メソッド呼び出し (obj.method())
                elif isinstance(node.func, astroid.Attribute):
                    # ここでは単純なケースのみ処理 (self.method())
                    if isinstance(node.func.expr, astroid.Name) and node.func.expr.name == 'self':
                        class_name = caller_name.split('.')[-2]  # Assuming format: module.class.method
                        method_name = node.func.attrname
                        class_method = f"{class_name}.{method_name}"
                        if class_method in module_functions.get(module_name, {}):
                            full_method_name = module_functions[module_name][class_method]
                            call_graph[caller_name].add(full_method_name)
            
            # 子ノードを再帰的に処理
            for child_node in node.get_children():
                find_calls_in_node(child_node, caller_name)
        
        # 関数定義を処理
        for node in module.body:
            if isinstance(node, astroid.FunctionDef):
                caller_name = f"{module_name}.{node.name}"
                for child_node in node.body:
                    find_calls_in_node(child_node, caller_name)
            
            # クラス内のメソッドを処理
            elif isinstance(node, astroid.ClassDef):
                class_name = node.name
                for method in node.body:
                    if isinstance(method, astroid.FunctionDef):
                        caller_name = f"{module_name}.{class_name}.{method.name}"
                        for child_node in method.body:
                            find_calls_in_node(child_node, caller_name)

    def on_tab_changed(self, event=None):
        """タブが切り替わったときに文字数を更新する"""
        # 現在のタブインデックスを取得
        current_tab_index = self.tab_control.index(self.tab_control.select())
        
        # タブに応じてテキストウィジェットを選択
        if current_tab_index == 0:  # 解析結果タブ
            text_widget = self.result_text
        elif current_tab_index == 1:  # 拡張解析タブ
            text_widget = self.extended_text
        elif current_tab_index == 2:  # プロンプト入力タブ
            text_widget = self.prompt_text
        else:
            return
        
        # テキスト内容を取得して文字数をカウント
        text_content = text_widget.get(1.0, tk.END)
        char_count = len(text_content) - 1  # 最後の改行文字を除く
        
        # 文字数表示を更新
        self.char_count_label.config(text=f"文字数: {char_count}")

    def create_tab_selection_panel(self):
        """タブ選択パネルを作成"""
        tab_selection_frame = ttk.Frame(self.right_frame)
        
        # タイトルラベル
        title_label = ttk.Label(tab_selection_frame, text="コピーするタブ:")
        title_label.pack(side="left", padx=5)
        
        # チェックボックスの変数と保存場所
        self.tab_checkboxes = {}
        self.tab_checkbox_vars = {}
        
        # 設定から前回のタブ選択状態を取得
        saved_tab_selection = self.config_manager.get_tab_selection()
        
        # 指定されたタブの並びに合わせてチェックボックスを追加
        for tab_name in ["解析結果", "拡張解析", "JSON出力", "プロンプト入力"]:
            # 保存された選択状態を使用、なければデフォルトでFalse
            is_selected = saved_tab_selection.get(tab_name, False)
            var = tk.BooleanVar(value=is_selected)
            self.tab_checkbox_vars[tab_name] = var
            
            # チェックボックスを作成
            checkbox = ttk.Checkbutton(tab_selection_frame, text=tab_name, variable=var, 
                                      command=self.save_tab_selection_state)
            checkbox.pack(side="left", padx=5)
            self.tab_checkboxes[tab_name] = checkbox
        
        return tab_selection_frame

    def save_tab_selection_state(self):
        """タブ選択状態を保存"""
        # 現在の選択状態を取得
        current_selection = {}
        for tab_name, var in self.tab_checkbox_vars.items():
            current_selection[tab_name] = var.get()
        
        # 設定に保存
        self.config_manager.set_tab_selection(current_selection)
    def copy_selected_tabs(self):
        """選択されたタブの内容をクリップボードにコピー"""
        # 指定されたタブの並びに合わせる
        tab_names = ["解析結果", "拡張解析", "プロンプト入力"]
        selected_content = []
        
        # 各タブのチェック状態を確認
        for tab_name in tab_names:
            if self.tab_checkbox_vars[tab_name].get():
                content = self.get_tab_content(tab_name)
                if content:
                    selected_content.append(f"## {tab_name}\n{content}\n\n")
        
        if selected_content:
            # コンテンツを結合してクリップボードにコピー
            clipboard_text = "".join(selected_content)
            pyperclip.copy(clipboard_text)
            messagebox.showinfo("情報", "選択したタブの内容をクリップボードにコピーしました。")
        else:
            messagebox.showinfo("情報", "コピーするタブが選択されていません。")

    def get_tab_content(self, tab_name):
        """タブ名に対応する内容を取得"""
        if tab_name == "解析結果":
            return self.result_text.get(1.0, tk.END).strip()
        elif tab_name == "拡張解析":
            return self.extended_text.get(1.0, tk.END).strip()
        elif tab_name == "JSON出力":
            return self.json_text.get(1.0, tk.END).strip()
        elif tab_name == "プロンプト入力":
            return self.prompt_text.get(1.0, tk.END).strip()
        return ""

    def toggle_exe_folder_skip(self):
        """EXEを含むフォルダのスキップ設定を変更"""
        skip_exe = self.skip_exe_folders.get()
        
        # ディレクトリツリービューの設定を更新
        if hasattr(self.dir_tree_view, 'skip_exe_folders'):
            self.dir_tree_view.skip_exe_folders = skip_exe
            
            # 現在のディレクトリが読み込まれている場合は再読み込み
            if self.current_dir:
                # 確認ダイアログを表示
                if messagebox.askyesno("確認", "設定を適用するには、現在のディレクトリを再読み込みする必要があります。続行しますか？"):
                    self.dir_tree_view.load_directory(self.current_dir)

    def setup_text_editor_shortcuts(self):
        """テキストエディタのショートカットとコンテキストメニューを設定"""
        # プロンプトエディタのショートカット設定
        self.setup_editor_shortcuts(self.prompt_text)
        
        # 解析結果エディタにもショートカットを追加（読み取り専用でも、コピーなどは可能）
        self.setup_editor_shortcuts(self.result_text)
        
        # 拡張解析エディタにもショートカットを追加
        self.setup_editor_shortcuts(self.extended_text)
        
        # テキスト変更イベントをバインド
        self.prompt_text.bind("<<Modified>>", self.on_text_modified)
        self.result_text.bind("<<Modified>>", self.on_text_modified)
        self.extended_text.bind("<<Modified>>", self.on_text_modified)

    def on_text_modified(self, event):
        """テキストが変更されたときに文字数を更新する"""
        # イベントが発生したウィジェットを取得
        text_widget = event.widget
        
        # 現在のタブインデックスを取得
        current_tab_index = self.tab_control.index(self.tab_control.select())
        
        # 現在のタブに対応するテキストウィジェットがイベントを発生させたものかチェック
        if (current_tab_index == 0 and text_widget == self.result_text) or \
           (current_tab_index == 1 and text_widget == self.extended_text) or \
           (current_tab_index == 2 and text_widget == self.prompt_text):
            
            # テキスト内容を取得して文字数をカウント
            text_content = text_widget.get(1.0, tk.END)
            char_count = len(text_content) - 1  # 最後の改行文字を除く
            
            # 文字数表示を更新
            self.char_count_label.config(text=f"文字数: {char_count}")
        
        # Modifiedフラグをリセット（次のイベント検出のため）
        text_widget.edit_modified(False)
        
    def on_tab_changed(self, event=None):
        """タブが切り替わったときに文字数を更新する"""
        # 現在のタブインデックスを取得
        current_tab_index = self.tab_control.index(self.tab_control.select())
        
        # タブに応じてテキストウィジェットを選択
        if current_tab_index == 0:  # 解析結果タブ
            text_widget = self.result_text
        elif current_tab_index == 1:  # 拡張解析タブ
            text_widget = self.extended_text
        elif current_tab_index == 2:  # JSONタブ
            text_widget = self.json_text
        elif current_tab_index == 3:  # プロンプト入力タブ
            text_widget = self.prompt_text
        else:
            return
        
        # テキスト内容を取得して文字数をカウント
        text_content = text_widget.get(1.0, tk.END)
        char_count = len(text_content) - 1  # 最後の改行文字を除く
        
        # 文字数表示を更新
        self.char_count_label.config(text=f"文字数: {char_count}")

    def setup_editor_shortcuts(self, text_widget):
        """テキストウィジェットにショートカットとコンテキストメニューを設定"""
        # ショートカットキーのバインド
        text_widget.bind("<Control-a>", lambda event: self.select_all(event, text_widget))
        text_widget.bind("<Control-c>", lambda event: self.copy_text(event, text_widget))
        text_widget.bind("<Control-x>", lambda event: self.cut_text(event, text_widget))
        text_widget.bind("<Control-v>", lambda event: self.paste_text(event, text_widget))
        text_widget.bind("<Control-z>", lambda event: self.undo_text(event, text_widget))
        text_widget.bind("<Control-y>", lambda event: self.redo_text(event, text_widget))
        text_widget.bind("<Control-s>", lambda event: self.save_current_prompt(event)) # プロンプト保存
        
        # Windows/Linuxの場合はShift+Deleteでカットも追加
        text_widget.bind("<Shift-Delete>", lambda event: self.cut_text(event, text_widget))
        
        # コンテキストメニュー作成
        context_menu = tk.Menu(text_widget, tearoff=0)
        context_menu.add_command(label="元に戻す", command=lambda: self.undo_text(None, text_widget), accelerator="Ctrl+Z")
        context_menu.add_command(label="やり直す", command=lambda: self.redo_text(None, text_widget), accelerator="Ctrl+Y")
        context_menu.add_separator()
        context_menu.add_command(label="切り取り", command=lambda: self.cut_text(None, text_widget), accelerator="Ctrl+X")
        context_menu.add_command(label="コピー", command=lambda: self.copy_text(None, text_widget), accelerator="Ctrl+C")
        context_menu.add_command(label="貼り付け", command=lambda: self.paste_text(None, text_widget), accelerator="Ctrl+V")
        context_menu.add_separator()
        context_menu.add_command(label="すべて選択", command=lambda: self.select_all(None, text_widget), accelerator="Ctrl+A")
        
        # 右クリックでコンテキストメニュー表示
        if sys.platform == 'darwin':  # macOS
            text_widget.bind("<Button-2>", lambda event: self.show_context_menu(event, context_menu))
        else:  # Windows/Linux
            text_widget.bind("<Button-3>", lambda event: self.show_context_menu(event, context_menu))
        
        # Undoを有効化
        try:
            text_widget.config(undo=True, maxundo=100, autoseparators=True)
        except tk.TclError:
            print("Undoの設定に失敗しました")

    def show_context_menu(self, event, menu):
        """コンテキストメニューを表示"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"  # イベントの伝播を停止

    def select_all(self, event, text_widget):
        """テキストをすべて選択"""
        text_widget.tag_add(tk.SEL, "1.0", tk.END)
        text_widget.mark_set(tk.INSERT, tk.END)
        text_widget.see(tk.INSERT)
        return "break"  # イベントの伝播を停止

    # def copy_text(self, event, text_widget):
        # """選択テキストをコピー"""
        # try:
            # selection = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            # self.root.clipboard_clear()
            # self.root.clipboard_append(selection)
        # except tk.TclError:
            # pass  # 選択されていない場合は何もしない
        # return "break"  # イベントの伝播を停止

    def cut_text(self, event, text_widget):
        """選択テキストを切り取り"""
        try:
            selection = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selection)
            text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass  # 選択されていない場合は何もしない
        return "break"  # イベントの伝播を停止

    def paste_text(self, event, text_widget):
        """クリップボードからテキストを貼り付け"""
        try:
            clipboard_text = self.root.clipboard_get()
            try:
                # 選択されているテキストを置き換え
                text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass  # 選択されていない場合は現在のカーソル位置に挿入
            text_widget.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            pass  # クリップボードが空または利用不可能な場合
        return "break"  # イベントの伝播を停止

    def undo_text(self, event, text_widget):
        """操作を元に戻す"""
        try:
            text_widget.edit_undo()
        except tk.TclError:
            pass  # 元に戻せる操作がない場合
        return "break"  # イベントの伝播を停止

    def redo_text(self, event, text_widget):
        """操作をやり直す"""
        try:
            text_widget.edit_redo()
        except tk.TclError:
            pass  # やり直せる操作がない場合
        return "break"  # イベントの伝播を停止

    def update_prompt_list(self):
        """プロンプト一覧を更新"""
        # ツリービューをクリア
        for item in self.prompt_tree.get_children():
            self.prompt_tree.delete(item)
        
        # プロンプト一覧を追加
        for prompt_id, prompt in self.prompt_manager.get_all_prompts().items():
            self.prompt_tree.insert("", "end", iid=prompt_id, text="", values=(prompt["name"],))
        
        # 現在のプロンプトIDが設定されていて、そのプロンプトが存在する場合に選択
        if hasattr(self, 'current_prompt_id') and self.current_prompt_id:
            if self.current_prompt_id in self.prompt_manager.get_all_prompts():
                self.prompt_tree.selection_set(self.current_prompt_id)
                self.prompt_tree.focus(self.current_prompt_id)
            
    # def on_prompt_selected(self, event):
        # """プロンプトが選択されたとき"""
        # selected_items = self.prompt_tree.selection()
        # if selected_items:
            # prompt_id = selected_items[0]
            # self.current_prompt_id = prompt_id
            
            # # プロンプト名と内容を表示
            # prompt_name = self.prompt_manager.get_prompt_name(prompt_id)
            # prompt_content = self.prompt_manager.get_prompt(prompt_id)
            
            # self.prompt_name_var.set(prompt_name)
            # self.prompt_text.delete(1.0, tk.END)
            # self.prompt_text.insert(tk.END, prompt_content)
            
            # # 現在のタブがプロンプト入力タブであれば文字数を更新
            # current_tab_index = self.tab_control.index(self.tab_control.select())
            # if current_tab_index == 2:  # プロンプト入力タブ
                # char_count = len(prompt_content)
                # self.char_count_label.config(text=f"文字数: {char_count}")

    def create_new_prompt(self):
        """新規プロンプトを作成"""
        prompt_id = self.prompt_manager.add_prompt("新規プロンプト", 
                                                  """# [ファイル/ディレクトリ名]の解析プロンプト

    以下のコード構造を分析して：
    [解析結果]

    ## 質問/指示
    [ここに質問や指示を入力してください]
    """)
        self.update_prompt_list()
        self.prompt_tree.selection_set(prompt_id)
        self.prompt_tree.focus(prompt_id)
        self.on_prompt_selected(None)

    def delete_current_prompt(self):
        """選択されているプロンプトを削除"""
        if self.current_prompt_id:
            if messagebox.askyesno("確認", "選択したプロンプトを削除しますか？"):
                if self.prompt_manager.delete_prompt(self.current_prompt_id):
                    # 削除成功
                    self.current_prompt_id = next(iter(self.prompt_manager.get_all_prompts()))
                    self.update_prompt_list()
                else:
                    messagebox.showinfo("情報", "最後のプロンプトは削除できません。")

    def save_current_prompt(self, event=None):
        """現在のプロンプトを保存"""
        if self.current_prompt_id:
            prompt_name = self.prompt_name_var.get()
            prompt_content = self.prompt_text.get(1.0, tk.END).strip()
            
            if not prompt_name:
                messagebox.showwarning("警告", "プロンプト名を入力してください。")
                return
            
            if self.prompt_manager.update_prompt(self.current_prompt_id, name=prompt_name, content=prompt_content):
                self.update_prompt_list()
                messagebox.showinfo("情報", f"プロンプト「{prompt_name}」を保存しました。")
                
                # 現在のタブがプロンプト入力タブであれば文字数を更新
                current_tab_index = self.tab_control.index(self.tab_control.select())
                if current_tab_index == 2:  # プロンプト入力タブ
                    char_count = len(prompt_content)
                    self.char_count_label.config(text=f"文字数: {char_count}")
                
            return "break"  # イベント伝播を停止（Ctrl+Sなどのショートカットを処理する場合）

    def toggle_display_options(self):
        """表示オプションの切り替え処理"""
        # アナライザーの設定を更新
        self.analyzer.include_imports = self.show_imports.get()
        self.analyzer.include_docstrings = self.show_docstrings.get()
        
        # 現在の選択に応じて再解析を実行
        if self.selected_file and os.path.isfile(self.selected_file):
            # 単一ファイルモード
            self.analyze_file(self.selected_file)
        elif self.current_dir:
            # ディレクトリモード
            self.analyze_selected()

    def toggle_imports_display(self):
        """インポート文の表示/非表示を切り替え、現在の解析結果を更新する"""
        # アナライザーの設定を更新
        self.analyzer.include_imports = self.show_imports.get()
        
        # 現在の選択に応じて再解析を実行
        if self.selected_file and os.path.isfile(self.selected_file):
            # 単一ファイルモード
            self.analyze_file(self.selected_file)
        elif self.current_dir:
            # ディレクトリモード
            self.analyze_selected()


    def load_last_session(self):
        """前回のセッション情報を読み込む"""
        last_file = self.config_manager.get_last_file()
        last_directory = self.config_manager.get_last_directory()
        
        if last_file and os.path.exists(last_file):
            # 前回のファイルを読み込む
            self.selected_file = last_file
            dir_path = os.path.dirname(last_file)
            self.current_dir = dir_path
            self.file_status.config(text=f"ファイル: {os.path.basename(last_file)}")
            
            # ディレクトリツリーを読み込み
            self.dir_tree_view.load_directory(dir_path)
            
            # ファイル内容を解析
            self.analyze_file(last_file)
        elif last_directory and os.path.exists(last_directory):
            # 前回のディレクトリを読み込む
            self.import_directory_path(last_directory)
    
    def on_window_resize(self, event):
        """ウィンドウサイズ変更時のイベントハンドラ"""
        # イベントがルートウィンドウからのものかチェック
        if event.widget == self.root:
            # 一定間隔でサイズ保存（タイマーをリセット）
            if hasattr(self, '_resize_timer'):
                self.root.after_cancel(self._resize_timer)
            self._resize_timer = self.root.after(500, self.save_window_size)
    
    def save_window_size(self):
        """現在のウィンドウサイズを設定に保存する"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        if width > 100 and height > 100:  # 最小サイズ以上の場合のみ保存
            self.config_manager.set_window_size(width, height)
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        # 未保存の変更がある場合は確認する
        if hasattr(self, 'prompt_modified') and self.prompt_modified:
            if not messagebox.askyesno("確認", "未保存の変更があります。\n変更を保存せずに終了しますか？"):
                # 保存してから終了
                if self.save_current_prompt():
                    pass  # 保存成功
                else:
                    # 保存に失敗した場合、終了をキャンセル
                    return
        
        # 現在のウィンドウサイズを保存
        self.save_window_size()

        # タブ選択状態を保存
        self.save_tab_selection_state()
        
        # 終了
        self.root.destroy()

    def save_current_prompt_without_confirm(self):
        """現在のプロンプトを確認なしで保存（終了時などに使用）"""
        if self.current_prompt_id:
            prompt_name = self.prompt_name_var.get()
            prompt_content = self.prompt_text.get(1.0, tk.END).strip()
            
            if not prompt_name:
                prompt_name = "無題のプロンプト"
            
            self.prompt_manager.update_prompt(self.current_prompt_id, name=prompt_name, content=prompt_content)

    def center_window(self):
        """ウィンドウを画面の中央に配置する"""
        self.root.update_idletasks()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"+{x}+{y}")
    
    def import_directory(self):
        """ディレクトリを選択してツリービューに表示"""
        dir_path = filedialog.askdirectory(title="Pythonファイルを含むディレクトリを選択")
        
        if dir_path:
            self.import_directory_path(dir_path)
    
    def import_directory_path(self, dir_path):
        """指定されたパスのディレクトリを読み込む"""
        # 選択されたファイルをリセット
        self.selected_file = None
        self.current_dir = dir_path
        self.dir_tree_view.load_directory(dir_path)
        self.file_status.config(text=f"ディレクトリ: {os.path.basename(dir_path)}")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"ディレクトリ '{dir_path}' を読み込みました。\n"
                              f"解析したいPythonファイルを選択して、[解析]ボタンをクリックしてください。\n\n"
                              f"ヒント: Shift+クリックでファイルやディレクトリを解析から除外できます。\n"
                              f"      ダブルクリックでファイルを選択できます。")
    
    def import_file(self):
        """単一のPythonファイルを選択"""
        file_path = filedialog.askopenfilename(
            title="Pythonファイルを選択",
            filetypes=[("Pythonファイル", "*.py"), ("すべてのファイル", "*.*")]
        )
        
        if file_path:
            # ファイル情報を設定
            self.selected_file = file_path
            dir_path = os.path.dirname(file_path)
            self.current_dir = dir_path
            self.file_status.config(text=f"ファイル: {os.path.basename(file_path)}")
            
            # 設定に保存
            self.config_manager.set_last_file(file_path)
            
            # ディレクトリツリーを読み込み
            self.dir_tree_view.load_directory(dir_path)
            
            # ファイル内容を解析
            self.analyze_file(file_path)
    
    def on_file_selected(self, file_path):
        """ツリービューでファイルが選択されたときのコールバック"""
        self.selected_file = file_path
        self.file_status.config(text=f"ファイル: {os.path.basename(file_path)}")
        
        # 設定に保存
        self.config_manager.set_last_file(file_path)
        
        # 解析結果タブに切り替え
        self.tab_control.select(0)  # 最初のタブ（解析結果タブ）を選択
        
        # ファイル内容を解析
        self.analyze_file(file_path)
        
        # プロンプトテンプレートを更新
        self.update_prompt_template(os.path.basename(file_path)) 
        
    def on_dir_selected(self, dir_path):
        """ツリービューでディレクトリが選択されたときのコールバック"""
        # 個別ファイル選択をクリアしてディレクトリ解析モードに切り替え
        self.selected_file = None
        self.current_dir = dir_path
        
        # 設定に保存
        self.config_manager.set_last_directory(dir_path)
        
        # ステータス更新
        self.file_status.config(text=f"ディレクトリ: {os.path.basename(dir_path)}")
        
        # 解析結果タブに切り替え
        self.tab_control.select(0)  # 最初のタブ（解析結果タブ）を選択
        
        # ディレクトリ内のファイルを解析
        self.analyze_directory(dir_path)
        
        # プロンプトテンプレートを更新
        self.update_prompt_template(os.path.basename(dir_path))        

    def update_prompt_template(self, name):
        """選択されたファイル/ディレクトリ名に基づいてプロンプトテンプレートを更新"""
        # デバッグ情報を追加
        print(f"プロンプトテンプレートの更新が呼び出されました。名前: {name}")
        print(f"現在のモード: {'ファイルモード' if self.selected_file else 'ディレクトリモード'}")
        
        if not hasattr(self, 'prompt_text') or not self.prompt_text:
            return
        
        # 現在のプロンプトテキストを取得
        current_prompt = self.prompt_text.get(1.0, tk.END)
        
        # 更新フラグ（変更があったかどうか）
        updated = False
        
        # 解析結果とJSON出力を取得
        analysis_result = self.result_text.get(1.0, tk.END) if hasattr(self, 'result_text') else ""
        json_output = self.json_text.get(1.0, tk.END) if hasattr(self, 'json_text') else ""
        
        # 置換処理を開始（複数のプレースホルダーを処理）
        updated_prompt = current_prompt
        
        # ファイル/ディレクトリ名の置換
        if "[ファイル/ディレクトリ名]" in updated_prompt:
            updated_prompt = updated_prompt.replace("[ファイル/ディレクトリ名]", name)
            updated = True
        elif "# main.pyの解析プロンプト" in updated_prompt and not self.selected_file:
            # ディレクトリモードなのに main.py が入っている場合は修正
            updated_prompt = updated_prompt.replace("main.py", name)
            updated = True
        
        # 解析結果の置換
        if "[解析結果]" in updated_prompt and analysis_result:
            updated_prompt = updated_prompt.replace("[解析結果]", analysis_result)
            updated = True
        
        # JSON出力の置換（新機能）
        if "[json出力]" in updated_prompt and json_output:
            updated_prompt = updated_prompt.replace("[json出力]", json_output)
            updated = True
        
        # 変更があった場合のみテキストを更新
        if updated:
            # テキストを更新
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(tk.END, updated_prompt)
            print(f"プロンプトテンプレートを更新しました: {name}")
            
            # 文字数も更新
            char_count = len(updated_prompt) - 1  # 最後の改行文字を除く
            self.prompt_char_count_var.set(f"文字数: {char_count}")
            
            # 現在表示されているタブがプロンプト入力タブであれば文字数ラベルも更新
            current_tab_index = self.tab_control.index(self.tab_control.select())
            if current_tab_index == 3:  # プロンプト入力タブ（インデックスが3）
                self.char_count_label.config(text=f"文字数: {char_count}")

    def analyze_directory(self, dir_path):
        """指定されたディレクトリ内のPythonファイルを解析"""
        if not hasattr(self.dir_tree_view, 'tree') or not self.dir_tree_view.tree or not self.dir_tree_view.tree.winfo_exists():
            return
        
        # ディレクトリ内の全ファイルを取得（Pythonファイルに限定しない）
        included_files = self.dir_tree_view.get_included_files()
        
        if not included_files:
            messagebox.showinfo("情報", "解析対象のファイルがありません。")
            return
        
        # Pythonファイルのみをフィルタリング
        python_files = [f for f in included_files if f.lower().endswith('.py')]
        
        if not python_files:
            messagebox.showinfo("情報", "解析対象のPythonファイルがありません。")
            return
        
        # 通常の解析実行
        result, char_count = self.analyzer.analyze_files(python_files)
        
        # 結果表示
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)
        self.result_highlighter.highlight()
        
        # 現在表示されているタブが解析結果タブの場合のみ文字数を更新
        current_tab_index = self.tab_control.index(self.tab_control.select())
        if current_tab_index == 0:  # 解析結果タブ
            self.char_count_label.config(text=f"文字数: {char_count}")
        
        # ステータス更新
        self.file_status.config(text=f"{len(python_files)} 個のPythonファイルを解析しました")
        
        # astroidによる拡張解析を実行
        self.perform_extended_analysis(python_files)
        
        # JSON出力を生成（追加）
        self.generate_json_output()

    def perform_extended_analysis(self, python_files):
        """astroidによる拡張解析を実行する（全ファイル統合版）"""
        try:
            if not python_files:
                self.extended_text.delete(1.0, tk.END)
                self.extended_text.insert(tk.END, "拡張解析対象のPythonファイルがありません。")
                return
                    
            # 解析結果を保存する辞書
            analysis_results = {}
            module_nodes = {}
            
                
            # プログレスウィンドウを表示
            progress_window = tk.Toplevel(self.root)
            progress_window.title("拡張解析中")
            progress_window.geometry("400x100")
            progress_window.transient(self.root)
                
            progress_label = ttk.Label(progress_window, text=f"ファイルを解析中... (0/{len(python_files)})")
            progress_label.pack(pady=10)
                
            progress_bar = ttk.Progressbar(progress_window, mode="determinate", maximum=100)
            progress_bar.pack(fill="x", padx=20)
                
            # ウィンドウを中央に配置
            progress_window.update_idletasks()
            x = self.root.winfo_rootx() + (self.root.winfo_width() - progress_window.winfo_width()) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - progress_window.winfo_height()) // 2
            progress_window.geometry(f"+{x}+{y}")
                
            # 統合解析レポート用の情報
            all_classes = []
            all_functions = []
            all_dependencies = {}
            all_inheritance = {}
            main_file = None
            
            # ディレクトリ構造を取得
            directory_structure = self.get_directory_structure(python_files)
                
            # Step 1: 各ファイルを個別に解析する
            for i, file_path in enumerate(python_files):
                try:
                    # プログレス更新
                    progress_pct = (i / len(python_files)) * 100
                    progress_bar["value"] = progress_pct
                    progress_label.config(text=f"ファイルを解析中... ({i+1}/{len(python_files)}): {os.path.basename(file_path)}")
                    progress_window.update()
                    
                    # ファイルを読み込む
                    with open(file_path, 'r', encoding='utf-8') as file:
                        code = file.read()
                    
                    # main関数やエントリーポイントを探す（大事なファイルを特定）
                    if 'if __name__ == "__main__"' in code or "main()" in code:
                        main_file = file_path
                    
                    # astroidでモジュールをパース
                    module = astroid.parse(code)
                    module_name = os.path.basename(file_path).replace('.py', '')
                    module_nodes[module_name] = module
                    
                    # ファイル個別の解析結果を取得
                    self.astroid_analyzer.reset()
                    file_result, _ = self.astroid_analyzer.analyze_code(code, os.path.basename(file_path))
                    
                    # 結果を蓄積
                    analysis_results[file_path] = {
                        'name': os.path.basename(file_path),
                        'classes': self.astroid_analyzer.classes.copy(),
                        'functions': self.astroid_analyzer.functions.copy(),
                        'dependencies': self.astroid_analyzer.dependencies.copy(),
                        'inheritance': self.astroid_analyzer.inheritance.copy()
                    }
                    
                    # 全体のリストに追加
                    all_classes.extend(self.astroid_analyzer.classes)
                    all_functions.extend(self.astroid_analyzer.functions)
                    all_dependencies.update(self.astroid_analyzer.dependencies)
                    all_inheritance.update(self.astroid_analyzer.inheritance)
                    
                except Exception as e:
                    print(f"ファイル {file_path} の解析中にエラー: {e}")
                    
                    traceback.print_exc()
            
            # プログレスウィンドウを閉じる
            progress_window.destroy()
            
            # Step 2: ファイル間の依存関係を解析
            # インポート関係を追跡
            file_dependencies = {}
            for module_name, module in module_nodes.items():
                file_dependencies[module_name] = set()
                for node in module.body:
                    if isinstance(node, astroid.Import):
                        for name in node.names:
                            imported_name = name[0].split('.')[0]
                            if imported_name in module_nodes:
                                file_dependencies[module_name].add(imported_name)
                    elif isinstance(node, astroid.ImportFrom):
                        if node.modname in module_nodes:
                            file_dependencies[module_name].add(node.modname)
            
            # 依存関係を解析する際にスキップすべき標準ライブラリや組み込み関数のリスト
            SKIP_DEPENDENCIES = {
                'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
                'open', 'range', 'enumerate', 'zip', 'map', 'filter',
                'os.path.join', 'os.path.exists', 'os.path.basename', 'os.path.dirname',
                'logging.info', 'logging.debug', 'logging.warning', 'logging.error'
                # GUI要素はスキップしない
            }
            
            # 依存関係をフィルタリング
            filtered_dependencies = {}
            for caller, callees in all_dependencies.items():
                filtered_callees = {callee for callee in callees if callee not in SKIP_DEPENDENCIES}
                if filtered_callees:  # 空でない場合のみ追加
                    filtered_dependencies[caller] = filtered_callees
            
            # フィルタリングした依存関係を使用
            all_dependencies = filtered_dependencies
            
            # ファイル間の依存関係もフィルタリング
            for module_name in file_dependencies:
                file_dependencies[module_name] = {
                    dep for dep in file_dependencies[module_name] 
                    if dep not in SKIP_DEPENDENCIES
                }
            
            # Step 3: 統合レポートの生成 - すべての詳細情報を省略してLLM向け構造化データのみ出力
            report = "# プロジェクト全体の拡張解析レポート\n\n"
            
            # LLM向け構造化データの出力
            report += "## LLM向け構造化データ\n"
            report += "```\n"
            
            # ディレクトリ構造を冒頭に挿入
            report += "# ディレクトリ構造\n"
            report += directory_structure
            report += "\n"
            
            # コンパクトなフォーマットでデータを出力
            compact_data = "# クラス一覧\n"
            for cls in all_classes:
                base_info = f" <- {', '.join(cls['base_classes'])}" if cls['base_classes'] else ""
                file_info = next((os.path.basename(f) for f, r in analysis_results.items() 
                               if any(c["name"] == cls["name"] for c in r["classes"])), "unknown")
                compact_data += f"{cls['name']}{base_info} ({file_info})\n"
                
                if cls['methods']:
                    compact_data += "  メソッド:\n"
                    for m in cls['methods']:
                        params = ", ".join(p['name'] for p in m['parameters'])
                        ret_type = f" -> {m['return_type']}" if m['return_type'] and m['return_type'] != "unknown" else ""
                        compact_data += f"    {m['name']}({params}){ret_type}\n"
                compact_data += "\n"

            compact_data += "# 関数一覧\n"
            for func in all_functions:
                params = ", ".join(p['name'] for p in func['parameters'])
                ret_type = f" -> {func['return_type']}" if func['return_type'] and func['return_type'] != "unknown" else ""
                file_info = next((os.path.basename(f) for f, r in analysis_results.items() 
                               if any(fn["name"] == func["name"] for fn in r["functions"])), "unknown")
                compact_data += f"{func['name']}({params}){ret_type} ({file_info})\n"
            compact_data += "\n"

            # 関数間の依存関係（主要なもののみ）
            if all_dependencies:
                compact_data += "# 主要な関数依存関係\n"
                # 依存の多いもの順に表示
                important_dependencies = sorted([(k, v) for k, v in all_dependencies.items() if v], 
                                             key=lambda x: len(x[1]), reverse=True)[:10]
                for caller, callees in important_dependencies:
                    compact_data += f"{caller} -> {', '.join(callees)}\n"
                compact_data += "\n"
            
            # コールグラフの生成と追加
            call_graph_text = self.generate_call_graph(python_files)
            # compact_data += "# コールグラフ\n"
            compact_data += call_graph_text
            compact_data += "\n"

            report += compact_data
            report += "```\n"
            
            # 拡張解析の結果を表示
            self.extended_text.delete(1.0, tk.END)
            self.extended_text.insert(tk.END, report)
            self.extended_highlighter.highlight()
            
            # 現在表示されているタブが拡張解析タブの場合のみ文字数を更新
            current_tab_index = self.tab_control.index(self.tab_control.select())
            if current_tab_index == 1:  # 拡張解析タブ
                char_count = len(report)
                self.char_count_label.config(text=f"文字数: {char_count}")
            
            # JSON出力を生成（拡張解析の後に呼び出し）
            self.generate_json_output()
            
        except ImportError:
            self.extended_text.delete(1.0, tk.END)
            self.extended_text.insert(tk.END, "astroidライブラリがインストールされていません。\n"
                                    "pip install astroid でインストールしてください。")
        except Exception as e:
            self.extended_text.delete(1.0, tk.END)
            error_msg = f"拡張解析中にエラーが発生しました:\n{str(e)}"
            print(error_msg)
            
            traceback.print_exc()
            self.extended_text.insert(tk.END, error_msg)

    def get_directory_structure(self, python_files):
        """ファイルリストからディレクトリ構造を生成する"""
        # ファイルのディレクトリを取得する
        if not python_files:
            return "ファイルがありません"
        
        # 共通のルートディレクトリを見つける
        file_dirs = [os.path.dirname(f) for f in python_files]
        common_root = os.path.commonpath(file_dirs) if file_dirs else ""
        
        # ディレクトリツリーを構築
        tree = {}
        for file_path in python_files:
            # ルートからの相対パスを取得
            rel_path = os.path.relpath(file_path, common_root)
            parts = rel_path.split(os.sep)
            
            # ツリー構造に追加
            current = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # ファイル
                    if "_files" not in current:
                        current["_files"] = []
                    current["_files"].append(part)
                else:  # ディレクトリ
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        # ツリー構造を文字列に変換
        result = []
        
        def print_tree(node, prefix="", is_last=True, indent=""):
            # ディレクトリ内のファイルとサブディレクトリを取得
            dirs = sorted([k for k in node.keys() if k != "_files"])
            files = sorted(node.get("_files", []))
            
            # 現在のディレクトリのファイルを出力
            for i, f in enumerate(files):
                is_last_file = (i == len(files) - 1) and not dirs
                result.append(f"{indent}{'└── ' if is_last_file else '├── '}{f}")
            
            # サブディレクトリを出力
            for i, d in enumerate(dirs):
                is_last_dir = (i == len(dirs) - 1)
                result.append(f"{indent}{'└── ' if is_last_dir else '├── '}{d}/")
                # 次のレベルのインデント
                next_indent = indent + ("    " if is_last_dir else "│   ")
                print_tree(node[d], prefix + d + "/", is_last_dir, next_indent)
        
        # ルートディレクトリ名を出力
        root_name = os.path.basename(common_root) or "root"
        result.append(f"{root_name}/")
        # ルート以下のツリーを出力
        print_tree(tree, indent="")
        
        return "\n".join(result)

    def analyze_file(self, file_path):
        """単一のファイルを解析"""
        try:
            # 通常の解析
            result, char_count = self.analyzer.analyze_file(file_path)
            
            # 結果表示
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            self.result_highlighter.highlight()
            
            # 現在表示されているタブが解析結果タブの場合のみ文字数を更新
            current_tab_index = self.tab_control.index(self.tab_control.select())
            if current_tab_index == 0:
                self.char_count_label.config(text=f"文字数: {char_count}")
            
            # ステータス更新
            self.file_status.config(text=f"ファイル: {os.path.basename(file_path)}")
            
            # 単一ファイルの拡張解析を実行
            self.perform_extended_analysis([file_path])
            
            # JSON出力を生成（追加）
            self.generate_json_output()
            
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの解析中にエラーが発生しました:\n{str(e)}")


    def analyze_selected(self):
        """選択されたファイルまたはディレクトリを解析"""
        # ファイルモードかディレクトリモードかを明示的に確認
        file_mode = self.selected_file and os.path.isfile(self.selected_file)
        
        # ファイルモードの場合は、そのファイルだけを解析
        if file_mode:
            self.analyze_file(self.selected_file)
            return
        
        # ディレクトリモードの場合は、含まれるPythonファイルのみを解析
        included_files = self.dir_tree_view.get_included_files(include_python_only=True)
        
        if not included_files:
            messagebox.showinfo("情報", "解析対象のPythonファイルがありません。\n"
                               "ディレクトリを選択し、Pythonファイルが含まれていることを確認してください。\n"
                               "または、Pythonファイルがすべて「除外」状態になっていないか確認してください。")
            return
        
        # 解析実行
        result, char_count = self.analyzer.analyze_files(included_files)
        
        # 結果表示
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)
        self.result_highlighter.highlight()
        self.char_count_label.config(text=f"文字数: {char_count}")
        
        # ステータス更新
        self.file_status.config(text=f"{len(included_files)} 個のPythonファイルを解析しました")
        
        # 拡張解析を実行
        self.perform_extended_analysis(included_files)
    
    def copy_to_clipboard(self):
        """解析結果とプロンプトをクリップボードにコピーする（選択されたタブに基づく）"""
        # 選択されたタブのチェック状態を取得
        selected_tabs = []
        for tab_name, var in self.tab_checkbox_vars.items():
            if var.get():
                selected_tabs.append(tab_name)
        
        # 選択されたタブがない場合は、現在表示されているタブを選択
        if not selected_tabs:
            current_tab_index = self.tab_control.index(self.tab_control.select())
            if current_tab_index == 0:
                selected_tabs.append("解析結果")
            elif current_tab_index == 1:
                selected_tabs.append("拡張解析")
            elif current_tab_index == 2:
                selected_tabs.append("JSON出力")
            elif current_tab_index == 3:
                selected_tabs.append("プロンプト入力")
        
        # 優先順位に従ってタブをソート（プロンプト入力を最初に）
        selected_tabs_ordered = []
        
        # プロンプト入力が選択されている場合は最初に追加
        if "プロンプト入力" in selected_tabs:
            selected_tabs_ordered.append("プロンプト入力")
            selected_tabs.remove("プロンプト入力")
        
        # 残りのタブを追加
        selected_tabs_ordered.extend(selected_tabs)
        
        # 選択されたタブの内容を結合
        combined_content = []
        for tab_name in selected_tabs_ordered:
            content = self.get_tab_content(tab_name)
            if content:
                if len(selected_tabs_ordered) > 1:  # 複数のタブが選択されている場合のみ見出しを追加
                    combined_content.append(f"## {tab_name}\n{content}\n\n")
                else:
                    combined_content.append(content)
        
        if combined_content:
            # コンテンツを結合してクリップボードにコピー
            clipboard_text = "".join(combined_content)
            pyperclip.copy(clipboard_text)
            messagebox.showinfo("情報", "選択したタブの内容をクリップボードにコピーしました。")
        else:
            messagebox.showinfo("情報", "コピーする内容がありません。")

    def on_file_selected(self, file_path):
        """ツリービューでファイルが選択されたときのコールバック"""
        self.selected_file = file_path
        self.file_status.config(text=f"ファイル: {os.path.basename(file_path)}")
        
        # 設定に保存
        self.config_manager.set_last_file(file_path)
        
        # 解析結果タブに切り替え
        self.tab_control.select(0)  # 最初のタブ（解析結果タブ）を選択
        
        # ファイル内容を解析
        self.analyze_file(file_path)
        
        # プロンプトテンプレートを更新
        self.update_prompt_template(os.path.basename(file_path))

    def on_dir_selected(self, dir_path):
        """ツリービューでディレクトリが選択されたときのコールバック"""
        # 個別ファイル選択をクリアしてディレクトリ解析モードに切り替え
        self.selected_file = None
        self.current_dir = dir_path
        
        # 設定に保存
        self.config_manager.set_last_directory(dir_path)
        
        # ステータス更新
        self.file_status.config(text=f"ディレクトリ: {os.path.basename(dir_path)}")
        
        # 解析結果タブに切り替え
        self.tab_control.select(0)  # 最初のタブ（解析結果タブ）を選択
        
        # ディレクトリ内のファイルを解析
        self.analyze_directory(dir_path)
        
        # プロンプトテンプレートを更新
        self.update_prompt_template(os.path.basename(dir_path))

    def export_to_json(self):
        """解析結果をJSONファイルにエクスポート"""
        # simple_json_converterをインポート
        import simple_json_converter
        
        # 現在の解析結果を取得
        result_text = self.result_text.get(1.0, "end-1c")
        
        if not result_text.strip():
            messagebox.showinfo("情報", "JSONに変換する解析結果がありません。")
            return
        
        # 保存先ファイル名の選択
        if self.selected_file:
            base_name = os.path.splitext(os.path.basename(self.selected_file))[0]
        else:
            base_name = "code_analysis"
        
        file_path = filedialog.asksaveasfilename(
            title="JSONファイルの保存先",
            initialdir=self.current_dir,
            initialfile=f"{base_name}.json",
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
        )
        
        if not file_path:
            return  # キャンセルされた場合
        
        try:
            # テキストをJSON構造に変換
            json_data = simple_json_converter.text_to_json_structure(result_text)
            
            # 拡張解析タブの内容があれば追加
            extended_text = self.extended_text.get(1.0, "end-1c")
            if extended_text.strip():
                json_data["extended_analysis"] = extended_text
            
            # JSONファイルとして保存
            message = simple_json_converter.save_as_json(json_data, file_path)
            messagebox.showinfo("情報", message)
            
        except Exception as e:
            messagebox.showerror("エラー", f"JSONエクスポート中にエラーが発生しました: {str(e)}")

    def generate_json_output(self):
        """現在の解析結果からJSON出力を生成してJSONタブに表示する"""
        
        # 現在の解析結果を取得
        result_text = self.result_text.get(1.0, "end-1c")
        extended_text = self.extended_text.get(1.0, "end-1c")
        
        if not result_text.strip():
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, "JSONに変換する解析結果がありません。")
            return
        
        try:
            # テキストをJSON構造に変換
            json_data = self.text_to_json_structure(result_text)
            
            # ディレクトリ構造をJSONの冒頭に追加
            if self.selected_file:
                # ファイルモードの場合は、そのファイルを含むディレクトリを取得
                python_files = [self.selected_file]
            else:
                # ディレクトリモードの場合は含まれるPythonファイルを取得
                python_files = self.dir_tree_view.get_included_files(include_python_only=True)
            
            # ディレクトリ構造を取得して行ごとの配列に変換
            if python_files:
                dir_structure_text = self.get_directory_structure(python_files)
                dir_structure_lines = dir_structure_text.split('\n')
                
                # 既存のディレクトリ構造を上書き
                json_data["directory_structure"] = dir_structure_lines
            
            # 拡張解析テキストがあれば追加
            if extended_text.strip():
                # LLM構造化データ部分を抽出して構造化
                extended_data = self.extract_llm_structured_data(extended_text)
                if extended_data:
                    json_data["extended_analysis"] = extended_data
            
            # JSON形式の文字列に変換して整形
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            
            # JSONタブに表示
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, json_string)
            
            # シンタックスハイライトを適用
            self.json_highlighter.highlight()
            
            # 現在表示されているタブがJSONタブの場合のみ文字数を更新
            current_tab_index = self.tab_control.index(self.tab_control.select())
            if current_tab_index == 2:  # JSONタブ (JSONタブが3番目)
                char_count = len(json_string)
                self.char_count_label.config(text=f"文字数: {char_count}")
            
        except Exception as e:
            traceback.print_exc()
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, f"JSON変換中にエラーが発生しました: {str(e)}")

class PromptManager:
    """プロンプトを管理するクラス"""
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.prompts = {}  # {id: {name: str, content: str}}
        self.load_prompts()
    
    def load_prompts(self):
        """設定ファイルからプロンプトを読み込む"""
        # configからプロンプトを取得
        prompts = self.config_manager.config.get("prompts", {})
        
        if not prompts:
            # デフォルトプロンプトを作成
            self.create_default_prompt()
        else:
            self.prompts = prompts
            print(f"{len(self.prompts)}個のプロンプトを読み込みました")
    
    def create_default_prompt(self):
        """デフォルトプロンプトを作成（最低1つは必要）"""
        default_prompts = {
            "default": {
                "name": "標準解析プロンプト",
                "content": """# [ファイル/ディレクトリ名]の解析プロンプト

以下のコード構造を分析して：
[解析結果]

## 質問/指示
[ここに質問や指示を入力してください]

## 特記事項
[特記事項があれば記入してください]
"""
            },
            "astroid": {
                "name": "拡張解析プロンプト（型・継承・依存関係）",
                "content": """# [ファイル/ディレクトリ名]の拡張解析プロンプト（astroid）

以下のコード構造と意味的関係を分析して、コードの理解と改善点を示してください。
構文構造だけでなく、型情報、継承関係、依存関係も含まれています：

[解析結果]

## 質問/指示
以下の観点からコードを分析してください：
1. クラス設計と継承関係の適切さ
2. メソッド間の依存関係と結合度
3. 型の一貫性と適切な使用
4. リファクタリングの機会
5. デザインパターンの検出と応用可能性

## コードの改善提案
[具体的な改善提案があれば記入してください]
"""
            },
            "llm_json": {
                "name": "LLM用JSON構造化データプロンプト",
                "content": """# [ファイル/ディレクトリ名]のLLM向け構造化データ解析

拡張解析レポートの最後に含まれるLLM向け構造化JSONデータを使用して、以下の質問に答えてください：

```json
[解析結果]
```

## 質問/指示
提供されたJSON構造データに基づいて、以下の点を分析してください：

1. このコードベースの主要なコンポーネントとその関係
2. クラス階層の設計とその効果
3. 関数/メソッド間の依存関係から見えるアーキテクチャの特徴
4. コードの改善点や最適化の可能性
5. このコードが採用している設計パターンやアーキテクチャパターン

## 特記事項
JSON構造化データは、astroidライブラリによって抽出された型情報、継承関係、依存関係を含んでいます。
"""
            }
        }
        
        self.prompts = default_prompts
        self.save_prompts()
        print("デフォルトプロンプトを作成しました")
    
    def save_prompts(self):
        """プロンプトを設定ファイルに保存"""
        self.config_manager.config["prompts"] = self.prompts
        self.config_manager.save_config()
        print("プロンプトを保存しました")
    
    def get_prompt(self, prompt_id):
        """IDからプロンプトを取得"""
        return self.prompts.get(prompt_id, {}).get("content", "")
    
    def get_prompt_name(self, prompt_id):
        """IDからプロンプト名を取得"""
        return self.prompts.get(prompt_id, {}).get("name", "")
    
    def add_prompt(self, name, content):
        """新しいプロンプトを追加"""
        # ユニークなIDを生成
        import uuid
        prompt_id = f"prompt_{str(uuid.uuid4())[:8]}"
        self.prompts[prompt_id] = {
            "name": name,
            "content": content
        }
        self.save_prompts()
        return prompt_id
    
    def update_prompt(self, prompt_id, name=None, content=None):
        """プロンプトを更新"""
        if prompt_id in self.prompts:
            if name is not None:
                self.prompts[prompt_id]["name"] = name
            if content is not None:
                self.prompts[prompt_id]["content"] = content
            self.save_prompts()
            return True
        return False
    
    def delete_prompt(self, prompt_id):
        """プロンプトを削除"""
        if prompt_id in self.prompts and len(self.prompts) > 1:
            del self.prompts[prompt_id]
            self.save_prompts()
            return True
        return False
    
    def get_all_prompts(self):
        """すべてのプロンプトを取得"""
        return self.prompts

def main():
    try:
        # ThemedTkを使用して洗練されたテーマを適用
        root = ThemedTk(theme="arc")  # 'arc'テーマを使用
    except Exception:
        # ThemedTkが利用できない場合は通常のTkを使用
        root = tk.Tk()
        messagebox.showinfo("情報", 
                           "ttkthemesライブラリがインストールされていないため、デフォルトテーマを使用します。\n"
                           "pip install ttkthemes でインストールすると、より洗練されたUIになります。")
    
    # 依存ライブラリのチェック
    missing_libs = []
    
    # astroidライブラリのチェック
    try:
        
        print(f"astroidライブラリが利用可能です: バージョン {astroid.__version__}")
    except ImportError:
        missing_libs.append("astroid")
        print("astroidライブラリがインストールされていません。拡張解析機能は無効になります。")
    
    # PILライブラリのチェック
    try:
        from PIL import Image, ImageTk
    except ImportError:
        missing_libs.append("Pillow")
        print("PILライブラリ (Pillow) がインストールされていません。テキストアイコンを使用します。")
    
    # 依存ライブラリのインストール案内
    if missing_libs:
        message = "以下のライブラリがインストールされていないため、一部の機能が制限されます：\n\n"
        
        if "astroid" in missing_libs:
            message += "- astroid: LLM向けの拡張解析機能（型推論、継承関係、依存関係）\n"
            message += "  インストール方法: pip install astroid\n\n"
        
        if "Pillow" in missing_libs:
            message += "- Pillow: カラーアイコン表示機能\n"
            message += "  インストール方法: pip install Pillow\n\n"
        
        message += "これらのライブラリをインストールすると、より高度な機能が利用できます。\n"
        message += "アプリは制限された機能で動作を続けます。"
        
        messagebox.showinfo("ライブラリの依存関係", message)
    
    # ウィンドウアイコンの設定
    try:
        # アイコンを探す複数の候補パスを設定
        icon_paths = []
        
        # 1. 実行ファイルと同じディレクトリのiconフォルダ
        exe_dir = os.path.dirname(os.path.abspath(__file__))
        icon_paths.append(os.path.join(exe_dir, "icon"))
        
        # 2. カレントディレクトリのiconフォルダ
        icon_paths.append(os.path.join(os.getcwd(), "icon"))
        
        # 3. PyInstallerでexe化された場合のパス
        try:
            import sys
            if getattr(sys, 'frozen', False):
                # PyInstaller環境
                exe_path = sys._MEIPASS
                icon_paths.append(os.path.join(exe_path, "icon"))
        except (AttributeError, ImportError):
            pass
        
        # 4. 親ディレクトリのiconフォルダ
        icon_paths.append(os.path.join(os.path.dirname(exe_dir), "icon"))
        
        # 5. 以前指定されていたパス（後方互換性のため）
        icon_paths.append(r"D:\OneDrive\In the middle of an update\code_analysis\icon")
        
        # アイコンファイル名のバリエーション
        icon_filenames = ["icons8-検査コード-48.png", "app_icon.png", "code_analyzer.png", "app.png", "icon.png"]
        
        # アイコンファイルを探す
        icon_path = None
        for dir_path in icon_paths:
            if not os.path.exists(dir_path):
                continue
                
            for fname in icon_filenames:
                path = os.path.join(dir_path, fname)
                if os.path.exists(path):
                    icon_path = path
                    break
            
            if icon_path:
                break
        
        # アイコンパスの存在確認
        if icon_path and os.path.exists(icon_path):
            # PILが利用可能な場合
            try:
                from PIL import Image, ImageTk
                icon_image = Image.open(icon_path)
                icon_photo = ImageTk.PhotoImage(icon_image)
                root.iconphoto(True, icon_photo)
                print(f"アイコンを設定しました: {icon_path}")
            except ImportError:
                # PILがない場合はiconbitmapを試す（.icoファイル用）
                if icon_path.lower().endswith('.ico'):
                    root.iconbitmap(icon_path)
                    print(f"ICOアイコンを設定しました: {icon_path}")
                else:
                    print("PILライブラリがないため、PNGアイコンを設定できません。")
        else:
            print("アプリケーションアイコンが見つかりませんでした。")
    except Exception as e:
        print(f"アイコン設定エラー: {e}")
    
    app = CodeAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
