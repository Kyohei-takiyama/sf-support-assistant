# Salesforce Support Assistant with AI

Salesforce ケースのインテリジェントなサポートアシスタントを AWS Lambda、Strands Agents、Salesforce LWC で実現したプロジェクトです。

## 🎯 概要

カスタマーサポート業務を AI で支援し、ケース解決時間の短縮と対応品質の向上を実現します。

### 主な機能

- 🤖 **AI ケース分析**: ケース内容を自動分析し、解決策を提案
- 🔍 **類似ケース検索**: 過去の類似ケースから解決パターンを発見
- 🌐 **外部情報統合**: Web 上の関連記事や既知問題情報を自動収集
- 💬 **AI チャット**: コンテキストを理解した対話型サポート
- ⚡ **リアルタイム連携**: Salesforce ユーティリティバーで即座に利用可能

## 🏗️ アーキテクチャ

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Salesforce    │    │   AWS Lambda     │    │  External APIs  │
│      LWC        │    │   Functions      │    │                 │
└────────┬────────┘    └────────┬─────────┘    └────────┬────────┘
         │                      │                        │
    ┌────▼────┐          ┌─────▼─────┐          ┌──────▼──────┐
    │ Support │          │   Main    │          │  Tavily API │
    │Assistant│◄────────►│  Agent    │◄────────►│ Web Search  │
    │Component│          │  Lambda   │          └──────────────┘
    └─────────┘          └─────┬─────┘
                               │
                         ┌─────▼─────┐
                         │Salesforce │
                         │API Lambda │
                         └─────┬─────┘
                               │
                         ┌─────▼─────┐
                         │  Strands  │
                         │  Agents   │
                         └───────────┘
```

## 📁 プロジェクト構造

```
sf-support-assistant/
├── agent-app/                  # AWS Lambda ベースの AI エージェント
│   ├── src/
│   │   ├── main_agent/        # メインエージェント (Strands Agents 統合)
│   │   ├── sf_api/            # Salesforce API 連携
│   │   └── web_search/        # Web検索機能 (Tavily API)
│   ├── terraform/             # インフラストラクチャ定義
│   └── Makefile              # デプロイ自動化
│
├── salesforce/                # Salesforce コンポーネント
│   └── force-app/
│       └── main/default/
│           ├── classes/       # Apex コントローラー
│           └── lwc/           # Lightning Web Components
│
├── CLAUDE.md                  # AI コード生成ガイド
└── README.md                  # このファイル
```

## 🚀 セットアップ

### 前提条件

- AWS アカウント
- Salesforce 開発者組織
- Terraform インストール済み
- Python 3.11+

### 1. 環境変数の設定

```bash
export SALESFORCE_INSTANCE_URL="https://your-instance.salesforce.com"
export SALESFORCE_CLIENT_ID="your-client-id"
export SALESFORCE_CLIENT_SECRET="your-client-secret"
export TAVILY_API_KEY="your-tavily-api-key"
```

### 2. AWS Lambda デプロイ

```bash
cd agent-app
make init    # Terraform 初期化
make deploy  # Lambda 関数とAPI Gateway をデプロイ
```

### 3. Salesforce コンポーネントデプロイ

```bash
cd salesforce
# Salesforce CLIでデプロイ
sf project deploy start
```

### 4. API エンドポイントの設定

Apex コントローラーの `API_ENDPOINT` をデプロイされた API Gateway URL に更新：

```apex
private static final String API_ENDPOINT = 'https://your-api-gateway-url/dev/agent';
```

## 💡 使い方

1. **ケース画面を開く**: Salesforce でケースレコードページを開く
2. **Support Assistant 起動**: ユーティリティバーから自動起動
3. **AI 分析確認**: ケース内容の自動分析結果を確認
4. **チャットで質問**: 具体的な解決方法を AI に質問
5. **参考情報確認**: 類似ケースや外部記事を参照

## 🛠️ 技術スタック

### Backend

- **AWS Lambda**: Python 3.11 サーバーレス関数
- **Strands Agents**: AI エージェントフレームワーク
- **AWS Bedrock**: Claude 3 による自然言語処理
- **Terraform**: インフラストラクチャ as Code

### Frontend

- **Lightning Web Components (LWC)**: モダンな UI コンポーネント
- **Apex**: サーバーサイド処理
- **SOSL**: 広範囲な類似ケース検索

### 外部サービス

- **Tavily API**: Web 検索と情報収集
- **Salesforce OAuth 2.0**: Client Credentials Flow による認証

## 🔧 開発コマンド

```bash
# Lambda 関数のパッケージング
make package

# インフラの変更確認
make plan

# デプロイ
make deploy

# リソースの削除
make destroy
```

## 📊 パフォーマンス

- **レスポンスタイム**: 平均 3-5 秒（AI 回答生成含む）
- **類似ケース検索**: 最大 15 件/クエリ × 3 キーワード
- **タイムアウト**: Lambda 120 秒、API Gateway 30 秒
