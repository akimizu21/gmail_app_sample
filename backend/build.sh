#!/usr/bin/env bash
set -o errexit

# pipとビルドツールのアップグレード
pip install --upgrade pip setuptools wheel

# 依存関係のインストール
pip install --no-cache-dir -r requirements.txt

# データベースマイグレーション
python create_tables.py