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
        シンプルな統合回答を生成
        """
        try:
            response = []

            response.append("【Salesforce サポート回答】")
            response.append("")

            # ケース基本情報
            response.append(f"ケースID: {case_analysis.get('case_id', 'N/A')}")
            response.append(f"件名: {case_analysis.get('subject', 'N/A')}")
            response.append(f"優先度: {case_analysis.get('priority', 'N/A')}")
            response.append(f"ステータス: {case_analysis.get('status', 'N/A')}")
            response.append("")

            # 質問への回答
            response.append("【ご質問への回答】")
            response.append(f"お問い合わせ: {question}")
            response.append("")

            # 類似ケースの情報
            similar_cases = case_analysis.get('similar_cases', [])
            if similar_cases:
                response.append("【類似ケースの参考情報】")
                for i, case in enumerate(similar_cases[:2], 1):
                    response.append(f"{i}. {case.get('Subject', 'N/A')}")
                    if case.get('Resolution'):
                        response.append(f"   解決方法: {case.get('Resolution')}")
                response.append("")

            # 推奨対応
            response.append("【推奨対応】")
            subject = case_analysis.get('subject', '').lower()
            if 'ログイン' in subject or 'セッション' in subject or 'タイムアウト' in subject:
                response.append("1. ブラウザのキャッシュとCookieをクリアしてください")
                response.append("2. 異なるブラウザ（Chrome、Firefox、Safari）でお試しください")
                response.append("3. インコグニトモードでアクセスしてみてください")
                response.append("4. ネットワーク接続の安定性を確認してください")
                response.append("5. VPN使用時は無効にしてお試しください")
            elif 'データ' in subject or 'インポート' in subject:
                response.append("1. ファイル形式（CSV、Excel）を確認してください")
                response.append("2. 文字エンコーディング（UTF-8）を確認してください")
                response.append("3. データの形式と必須項目を確認してください")
            else:
                response.append("1. 問題の詳細な再現手順をご教示ください")
                response.append("2. エラーメッセージのスクリーンショットをお送りください")
                response.append("3. 使用している環境（ブラウザ、OS）をお教えください")

            response.append("")
            response.append("追加のサポートが必要でしたら、お気軽にお申し付けください。")

            return "\n".join(response)

        except Exception as e:
            print(f"Simple response generation error: {str(e)}")
            return "申し訳ございませんが、回答生成でエラーが発生しました。手動でのサポートをご提供いたします。"

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
            # プロンプトの構築
            context_prompt = f"""
あなたはSalesforceのカスタマーサポートエージェントです。
以下の情報を基に、顧客からの質問に対する適切なサポート回答を生成してください。

## ケース情報:
- ケースID: {case_analysis.get('case_id', 'N/A')}
- 件名: {case_analysis.get('subject', 'N/A')}
- 説明: {case_analysis.get('description', 'N/A')}
- 優先度: {case_analysis.get('priority', 'N/A')}
- ステータス: {case_analysis.get('status', 'N/A')}
- 顧客: {case_analysis.get('account_name', 'N/A')}

## 類似ケース:
{json.dumps(case_analysis.get('similar_cases', []), ensure_ascii=False, indent=2)}

## 外部検索結果:
{json.dumps(search_results, ensure_ascii=False, indent=2)}

## 顧客からの質問:
{question}

この情報を統合して、具体的で実行可能な解決手順を含む回答を生成してください。
日本語で、顧客に優しく、プロフェッショナルな対応でお答えください。

必要に応じて以下のツールを使用してください：
- get_salesforce_case_details: ケースの詳細情報を取得
- find_similar_salesforce_cases: 類似ケースを検索
- search_external_knowledge: 外部ナレッジベースを検索
"""

            # Strands Agent で回答生成
            response = self.support_agent(context_prompt)

            return response

        except Exception as e:
            print(f"Strands Agent response generation error: {str(e)}")
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