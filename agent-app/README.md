# Salesforce Support Assistant

AI を活用した Salesforce カスタマーサポート支援システム

## 概要

Salesforce Support Assistant は、AWS Lambda、Strands Agents、AWS Bedrock を使用して構築されたサーバーレスアプリケーションです。Salesforce のケース情報を分析し、類似ケースの検索と外部情報の収集を行い、AI が統合的なサポート回答を生成します。

## 主な機能

- 🔍 **ケース分析**: Salesforce ケースの詳細情報を自動取得・分析
- 🔄 **類似ケース検索**: 過去の解決済みケースから類似パターンを特定
- 🌐 **外部情報検索**: Tavily API を使用して関連する既知問題や解決策を検索
- 🤖 **AI 回答生成**: AWS Bedrock (Claude 3) による統合的な解決策の提案
- 📋 **ワークフロー推奨**: 優先度やパターンに基づく次のアクションの提案

## アーキテクチャ

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Client    │────▶│  API Gateway    │────▶│ Main Agent   │
└─────────────┘     └─────────────────┘     │   Lambda     │
                                             └──────┬───────┘
                                                    │
                    ┌───────────────────────────────┴────────────────────┐
                    │                                                    │
                    ▼                                                    ▼
            ┌──────────────┐                                    ┌──────────────┐
            │ SF API       │                                    │ Web Search   │
            │ Lambda       │                                    │ Lambda       │
            └──────────────┘                                    └──────────────┘
                    │                                                    │
                    ▼                                                    ▼
            ┌──────────────┐                                    ┌──────────────┐
            │ Salesforce   │                                    │ Tavily API   │
            └──────────────┘                                    └──────────────┘
```

### コンポーネント

1. **Main Agent Lambda**: Strands Agents を使用したメインオーケストレーター
2. **Salesforce API Lambda**: OAuth 2.0 Client Credentials Flow による Salesforce 連携
3. **Web Search Lambda**: Tavily API による外部情報検索

## 技術スタック

- **インフラ**: AWS (Lambda, API Gateway, IAM)
- **IaC**: Terraform
- **言語**: Python 3.11
- **AI フレームワーク**: [Strands Agents](https://strandsagents.com/0.1.x/user-guide/quickstart/)
- **AI モデル**: AWS Bedrock (Claude 3 Sonnet/Haiku)
- **外部 API**: Salesforce API, Tavily API

## セットアップ

### 前提条件

- AWS アカウント
- Terraform >= 1.0
- Python 3.11
- Salesforce 組織と Connected App
- Tavily API キー

### 環境変数の設定

`terraform/terraform.tfvars` を作成:

```hcl
# AWS設定
aws_region = "ap-northeast-1"
project_name = "sf-support-assistant"
environment = "dev"

# Salesforce設定
salesforce_instance_url = "https://your-instance.salesforce.com"
salesforce_client_id = "your_connected_app_client_id"
salesforce_client_secret = "your_connected_app_client_secret"

# API Keys
tavily_api_key = "your_tavily_api_key"
```

### Salesforce Connected App の設定

1. Salesforce の設定から「アプリケーションマネージャ」を開く
2. 「新規接続アプリケーション」を作成
3. OAuth 設定:
   - 「OAuth 設定の有効化」をチェック
   - コールバック URL: `https://localhost` (Client Credentials Flow では使用しない)
   - 選択した OAuth 範囲:
     - `api` - API へのアクセス
     - `refresh_token` - いつでもリフレッシュトークンを実行
   - 「クライアントの資格情報フローの有効化」をチェック
4. 作成後、コンシューマ鍵とコンシューマの秘密を取得

## よく使うコマンド

```bash
# 初回セットアップ
make init

# デプロイ（パッケージング + Terraform適用）
make deploy

# Lambda関数のみパッケージング
make package

# インフラの変更をプレビュー
make plan

# インフラを削除
make destroy

# パッケージファイルをクリーンアップ
make clean

# Lambda関数を強制更新（権限が消える可能性あり）
make force-update

# Lambda関数のコードのみ更新（権限は保持）
make update-code

# API Gateway Lambda権限を修正
make fix-permissions
```

### 推奨される更新方法

通常のコード更新では、権限が保持される `make update-code` を使用することを推奨します：

```bash
# コードを修正後
make update-code
```

もしAPI Gateway権限エラーが発生した場合：

```bash
make fix-permissions
```

## デプロイ

```bash
# 初回セットアップ
make init

# デプロイ（パッケージング + インフラ構築）
make deploy

# インフラのみ更新
make apply

# 削除
make destroy
```

## 使用方法

### API エンドポイント

```
POST https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/agent
```

### リクエスト例

```json
{
  "case_id": "5001234567890ABC",
  "question": "このエラーの解決方法を教えてください"
}
```

### レスポンス例

```json
{
  "case_analysis": {
    "case_id": "5001234567890ABC",
    "subject": "ログインエラーが発生",
    "description": "...",
    "priority": "High",
    "status": "New",
    "similar_cases": [...]
  },
  "external_info": {
    "search_query": "ログインエラー 解決方法",
    "results": [...]
  },
  "ai_response": "このログインエラーについて、以下の解決手順をお試しください...",
  "recommendations": [
    {
      "type": "immediate_action",
      "description": "高優先度ケースです。1時間以内に初回対応を行ってください。"
    }
  ]
}
```

## 開発

### ディレクトリ構成

```
.
├── terraform/          # インフラ定義
├── src/
│   ├── main_agent/    # メインエージェント
│   │   ├── agents/    # エージェントモジュール
│   │   │   ├── record_analyzer.py
│   │   │   ├── workflow_advisor.py
│   │   │   ├── integration_manager.py
│   │   │   └── strands_tools.py
│   │   └── lambda_function.py
│   ├── sf_api/        # Salesforce API
│   └── web_search/    # Web 検索
└── Makefile
```

### 主要コマンド

```bash
make help      # ヘルプ表示
make package   # Lambda 関数のパッケージング
make plan      # Terraform 実行計画の確認
make test      # テスト実行
make clean     # ビルドアーティファクトの削除
```

## カスタマイズ

### Strands Agent のプロンプト変更

`src/main_agent/agents/integration_manager.py` の `SUPPORT_SYSTEM_PROMPT` を編集:

```python
SUPPORT_SYSTEM_PROMPT = """
あなたはSalesforceのカスタマーサポートエージェントです。
# カスタマイズしたプロンプト...
"""
```

### カスタムツールの追加

`src/main_agent/agents/strands_tools.py` に新しいツールクラスを追加:

```python
class CustomTool(Tool):
    name = "custom_tool"
    description = "カスタムツールの説明"

    def run(self, **kwargs):
        # 実装
        pass
```

## セキュリティ

- OAuth 2.0 Client Credentials Flow によるサーバー間認証
- IAM ロールによる最小権限の原則
- 環境変数による機密情報の管理
- API Gateway での CORS 設定

## トラブルシューティング

### Lambda タイムアウト

デフォルトのタイムアウトは以下の通り:

- Main Agent: 60 秒
- SF API: 30 秒
- Web Search: 30 秒

必要に応じて `terraform/lambda.tf` で調整してください。

### Salesforce API エラー

1. Connected App の設定を確認
2. Client ID/Secret が正しいか確認
3. API バージョン（v63.0）がサポートされているか確認

## 参考資料

- [Strands Agents Documentation](https://strandsagents.com/0.1.x/user-guide/quickstart/)
- [Salesforce REST API Documentation](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Tavily API Documentation](https://tavily.com/docs)
