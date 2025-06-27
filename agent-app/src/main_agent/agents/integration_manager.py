import json
import os
import boto3
import logging
try:
    from strands_agents import Agent
    from strands_agents_tools import calculator, current_time, python_repl
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False

from .record_analyzer import RecordAnalyzer
from .workflow_advisor import WorkflowAdvisor

# ログ設定
logger = logging.getLogger(__name__)

class IntegrationManager:
    """
    各エージェントを統合し、サポートリクエストを処理するメインマネージャー
    """

    def __init__(self):
        logger.info("Initializing IntegrationManager")
        
        # Lambda クライアント初期化
        logger.info("Setting up Lambda client")
        self.lambda_client = boto3.client('lambda')
        
        # 各コンポーネントの初期化
        logger.info("Initializing RecordAnalyzer")
        self.record_analyzer = RecordAnalyzer(self.lambda_client)
        
        logger.info("Initializing WorkflowAdvisor")
        self.workflow_advisor = WorkflowAdvisor(self.lambda_client)

        # Lambda関数名を環境変数から取得
        self.sf_function_name = os.environ.get('SF_API_FUNCTION_NAME')
        self.search_function_name = os.environ.get('WEB_SEARCH_FUNCTION_NAME')
        
        logger.info(f"SF API Function: {self.sf_function_name}")
        logger.info(f"Web Search Function: {self.search_function_name}")

        # Strands Agent の初期化（利用可能な場合）
        if STRANDS_AVAILABLE:
            logger.info("Strands Agents available - initializing support agent")
            self.support_agent = self._initialize_support_agent()
        else:
            logger.warning("Strands Agents not available - using simple implementation")
            self.support_agent = None
            
        logger.info("IntegrationManager initialization completed")

    def process_support_request(self, case_id, question):
        """
        サポートリクエストを処理し、統合された回答を生成
        """
        logger.info(f"Starting support request processing for case: {case_id}")
        logger.debug(f"Question: {question}")
        
        try:
            # 1. ケースレコードの分析
            logger.info("Step 1: Starting case record analysis")
            case_analysis = self.record_analyzer.analyze_case(case_id)
            logger.info(f"Case analysis completed. Status: {'success' if not case_analysis.get('error') else 'error'}")
            if case_analysis.get('error'):
                logger.error(f"Case analysis error: {case_analysis.get('error')}")

            # 2. 関連する外部情報の検索
            logger.info("Step 2: Starting external information search")
            case_subject = case_analysis.get('subject', '')
            case_description = case_analysis.get('description', '')
            logger.debug(f"Search terms - Subject: {case_subject}, Description length: {len(case_description)}")
            
            search_results = self.workflow_advisor.search_external_info(case_subject, case_description)
            logger.info(f"External search completed. Results count: {len(search_results.get('results', {}).get('results', []))}")

            # 3. 統合回答の生成
            logger.info("Step 3: Starting AI response generation")
            if STRANDS_AVAILABLE and self.support_agent:
                logger.info("Using Strands Agent for response generation")
                integrated_response = self._generate_strands_response(
                    case_analysis, search_results, question
                )
            else:
                logger.info("Using simple response generation (Strands not available)")
                integrated_response = self._generate_simple_response(
                    case_analysis, search_results, question
                )
            
            logger.info(f"AI response generated. Length: {len(integrated_response)} chars")

            # 4. 推奨事項の生成
            logger.info("Step 4: Generating recommendations")
            recommendations = self._generate_recommendations(case_analysis, search_results)
            logger.info(f"Generated {len(recommendations)} recommendations")

            final_response = {
                'case_analysis': case_analysis,
                'external_info': search_results,
                'ai_response': integrated_response,
                'recommendations': recommendations
            }
            
            logger.info("Support request processing completed successfully")
            return final_response

        except Exception as e:
            logger.error(f"Integration error: {str(e)}", exc_info=True)
            raise e

    def _generate_simple_response(self, case_analysis, search_results, question):
        """
        シンプルな統合回答を生成（質問に応じた動的な回答）
        """
        try:
            import time
            response = []

            # タイムスタンプを含めて回答の一意性を確保
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            response.append("【Salesforce サポート回答】")
            response.append(f"回答日時: {timestamp}")
            response.append("")

            # ケース基本情報
            response.append(f"ケースID: {case_analysis.get('case_id', 'N/A')}")
            response.append(f"件名: {case_analysis.get('subject', 'N/A')}")
            response.append(f"優先度: {case_analysis.get('priority', 'N/A')}")
            response.append(f"ステータス: {case_analysis.get('status', 'N/A')}")
            response.append("")

            # 質問への個別回答
            response.append("【ご質問への回答】")
            response.append(f"お問い合わせ: {question}")
            response.append("")
            
            # 質問内容に基づく具体的な回答を生成
            question_lower = question.lower()
            subject_lower = case_analysis.get('subject', '').lower()
            
            if any(keyword in question_lower for keyword in ['どうすれば', 'どうやって', '方法', 'やり方']):
                response.append("【解決方法】")
                if any(keyword in subject_lower or keyword in question_lower for keyword in ['ログイン', 'セッション', 'タイムアウト']):
                    response.extend([
                        "セッションタイムアウトの問題を解決するために、以下の手順をお試しください：",
                        "",
                        "1. **ブラウザの設定確認**",
                        "   - ブラウザのキャッシュとCookieを完全にクリアしてください",
                        "   - セキュリティ設定でJavaScriptが有効になっていることを確認してください",
                        "",
                        "2. **ネットワーク環境の確認**",
                        "   - 安定したネットワーク接続を使用してください",
                        "   - VPNを使用している場合は、一時的に無効にしてお試しください",
                        "",
                        "3. **異なる環境でのテスト**",
                        "   - 別のブラウザ（Chrome、Firefox、Safari、Edge）でお試しください",
                        "   - インコグニトモード/プライベートブラウジングモードをお試しください",
                        "",
                        "4. **Salesforce側の設定確認**",
                        "   - システム管理者にセッションタイムアウト設定を確認していただいてください",
                        "   - ユーザープロファイルのログイン時間制限を確認してください"
                    ])
                elif any(keyword in subject_lower or keyword in question_lower for keyword in ['データ', 'インポート', '取り込み']):
                    response.extend([
                        "データインポートの問題を解決するために、以下の手順をお試しください：",
                        "",
                        "1. **ファイル形式の確認**",
                        "   - CSVファイルの場合：UTF-8エンコーディングで保存されていることを確認",
                        "   - 区切り文字がカンマ（,）になっていることを確認",
                        "",
                        "2. **データ形式の確認**",
                        "   - 必須項目がすべて入力されていることを確認",
                        "   - 日付形式がSalesforceの要求形式（YYYY-MM-DD）になっていることを確認",
                        "   - 文字数制限を超えていないことを確認",
                        "",
                        "3. **インポート設定の確認**",
                        "   - 適切なオブジェクト（リード、商談、取引先など）が選択されていることを確認",
                        "   - フィールドマッピングが正しく設定されていることを確認"
                    ])
                else:
                    response.extend([
                        "問題を解決するために、以下の一般的な手順をお試しください：",
                        "",
                        "1. **問題の詳細確認**",
                        "   - エラーメッセージの正確な内容をご確認ください",
                        "   - 問題が発生する具体的な手順をお教えください",
                        "",
                        "2. **環境の確認**",
                        "   - 使用しているブラウザとバージョンをお教えください",
                        "   - 他のユーザーでも同様の問題が発生するかご確認ください",
                        "",
                        "3. **基本的なトラブルシューティング**",
                        "   - ページの再読み込み（F5キー）をお試しください",
                        "   - 別のブラウザでの動作をご確認ください"
                    ])
            elif any(keyword in question_lower for keyword in ['なぜ', '原因', '理由']):
                response.append("【原因の分析】")
                response.extend([
                    f"「{case_analysis.get('subject', '')}」の問題について、考えられる原因は以下の通りです：",
                    "",
                    "1. **技術的要因**",
                    "   - システムの一時的な不具合",
                    "   - ネットワーク接続の問題",
                    "   - ブラウザの互換性問題",
                    "",
                    "2. **設定要因**",
                    "   - ユーザー権限の不足",
                    "   - セキュリティ設定の制限",
                    "   - カスタム設定の影響",
                    "",
                    "3. **データ要因**",
                    "   - 入力データの形式問題",
                    "   - 必須項目の未入力",
                    "   - データ量の制限超過"
                ])
            else:
                response.append("【対応方法】")
                response.extend([
                    "ご質問の内容に基づき、以下の対応をお勧めいたします：",
                    "",
                    "1. 詳細な状況をお聞かせください",
                    "2. エラーメッセージがある場合はスクリーンショットをお送りください",
                    "3. 問題の再現手順を詳しくお教えください"
                ])

            # 類似ケースの情報
            similar_cases = case_analysis.get('similar_cases', [])
            if similar_cases:
                response.append("")
                response.append("【参考：類似ケース】")
                for i, case in enumerate(similar_cases[:2], 1):
                    response.append(f"{i}. ケース#{case.get('CaseNumber', 'N/A')}: {case.get('Subject', 'N/A')}")
                    if case.get('Status'):
                        response.append(f"   ステータス: {case.get('Status')}")

            # 外部情報がある場合
            external_results = search_results.get('results', {}).get('results', [])
            if external_results:
                response.append("")
                response.append("【参考：関連情報】")
                for i, result in enumerate(external_results[:2], 1):
                    response.append(f"{i}. {result.get('title', '関連記事')}")
                    response.append(f"   URL: {result.get('url', '')}")

            response.append("")
            response.append("さらに詳しいサポートが必要でしたら、お気軽にお申し付けください。")

            return "\n".join(response)

        except Exception as e:
            logger.error(f"Simple response generation error: {str(e)}")
            return f"申し訳ございませんが、回答生成でエラーが発生しました。時刻: {time.strftime('%H:%M:%S')}。手動でのサポートをご提供いたします。"

    def _initialize_support_agent(self):
        """
        Strands Agent を初期化
        """
        try:
            from .strands_tools import get_salesforce_case_details, find_similar_salesforce_cases, search_external_knowledge

            # 利用可能なツールを設定
            tools = [
                get_salesforce_case_details,
                find_similar_salesforce_cases,
                search_external_knowledge,
                calculator,
                current_time,
                python_repl
            ]

            return Agent(tools=tools)
        except Exception as e:
            print(f"Failed to initialize Strands Agent: {str(e)}")
            return None

    def _generate_strands_response(self, case_analysis, search_results, question):
        """
        Strands Agent を使用して回答を生成
        """
        try:
            import time
            import uuid
            
            # 一意なセッションIDを生成して過去のコンテキストを分離
            session_id = str(uuid.uuid4())[:8]
            timestamp = int(time.time())
            
            # プロンプトの構築（毎回新しいコンテキストとして構築）
            context_prompt = f"""
[セッション ID: {session_id}, タイムスタンプ: {timestamp}]

あなたはSalesforceのカスタマーサポートエージェントです。
これは新しい質問セッションです。過去の回答に依存せず、以下の情報のみを基に、顧客からの質問に対する新しいサポート回答を生成してください。

## 現在のケース情報:
- ケースID: {case_analysis.get('case_id', 'N/A')}
- 件名: {case_analysis.get('subject', 'N/A')}
- 説明: {case_analysis.get('description', 'N/A')}
- 優先度: {case_analysis.get('priority', 'N/A')}
- ステータス: {case_analysis.get('status', 'N/A')}
- 顧客: {case_analysis.get('account_name', 'N/A')}

## 現在の類似ケース:
{json.dumps(case_analysis.get('similar_cases', []), ensure_ascii=False, indent=2)}

## 現在の外部検索結果:
{json.dumps(search_results, ensure_ascii=False, indent=2)}

## 顧客からの現在の質問:
{question}

**重要**: この質問に特化した新しい回答を生成してください。質問の内容に応じて、具体的で実行可能な解決手順を含む回答を作成してください。
日本語で、顧客に優しく、プロフェッショナルな対応でお答えください。

質問の種類に応じて以下の観点を含めてください：
- 技術的な問題の場合：トラブルシューティング手順
- 操作方法の場合：ステップバイステップの説明
- 設定に関する場合：設定変更の具体的な手順
- エラーの場合：エラーの原因と解決方法

必要に応じて以下のツールを使用してください：
- get_salesforce_case_details: 追加のケース詳細情報を取得
- find_similar_salesforce_cases: 異なるキーワードで類似ケースを検索
- search_external_knowledge: 質問に関連する外部ナレッジベースを検索
"""

            # Strands Agent で回答生成
            response = self.support_agent(context_prompt)

            return response

        except Exception as e:
            logger.error(f"Strands Agent response generation error: {str(e)}")
            # フォールバックとしてシンプル版を使用
            return self._generate_simple_response(case_analysis, search_results, question)


    def _generate_recommendations(self, case_analysis, search_results):
        """
        推奨アクションを生成
        """
        recommendations = []

        # 緊急度に基づく推奨
        if case_analysis.get('priority') == 'High':
            recommendations.append({
                'type': 'escalation',
                'message': '高優先度のケースです。必要に応じてマネージャーにエスカレーションを検討してください。'
            })

        # 類似ケースがある場合の推奨
        if case_analysis.get('similar_cases'):
            recommendations.append({
                'type': 'reference',
                'message': '類似ケースが見つかりました。過去の解決パターンを参考にしてください。'
            })

        # 外部情報がある場合の推奨
        if search_results.get('results'):
            recommendations.append({
                'type': 'external_info',
                'message': '製品の既知問題や最新情報が見つかりました。詳細を確認してください。'
            })

        return recommendations