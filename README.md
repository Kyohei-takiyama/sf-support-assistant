# Salesforce Support Assistant Project

このプロジェクトは、Salesforce サポート業務を効率化するためのエージェントアプリケーションです。

## プロジェクト構造

```
sf-support-assistant/
├── agent-app/          # AWS Lambda/API Gateway ベースのAIエージェントアプリケーション
│   ├── src/           # Lambda関数のソースコード
│   ├── terraform/     # インフラストラクチャのコード
│   └── README.md      # エージェントアプリの詳細ドキュメント
│
├── salesforce/         # Salesforce関連のコードとデモデータ
│
└── README.md          # このファイル
```

## 各コンポーネントの説明

### agent-app/

AWS 上で動作するサーバーレス AI エージェントアプリケーション。以下の機能を提供：

- **Salesforce 連携**: ケース情報の取得と分析
- **AI 回答生成**: Strands Agents を使用した自動回答
- **外部情報検索**: Tavily API を使用した Web 検索
- **REST API**: API Gateway を通じたエンドポイント

詳細は[agent-app/README.md](agent-app/README.md)を参照してください。

### salesforce/

Salesforce 側のリソース：

## セットアップ

### 1. エージェントアプリのデプロイ

```bash
cd agent-app
make deploy
```

## 開発環境

- **AWS**: Lambda (Python 3.11), API Gateway, Terraform
- **Salesforce**: Apex, SOQL
- **AI/ML**: Strands Agents, Tavily API
