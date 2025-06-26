import json
import os
import boto3
from strands import Agent
from strands_tools import http_request,calculator, current_time, python_repl
from .record_analyzer import RecordAnalyzer
from .workflow_advisor import WorkflowAdvisor
from .strands_tools import create_strands_tools

class IntegrationManager:
    """
    各エージェントを統合し、サポートリクエストを処理するメインマネージャー
    """

    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.record_analyzer = RecordAnalyzer(self.lambda_client)
        self.workflow_advisor = WorkflowAdvisor(self.lambda_client)

        # Lambda関数名を環境変数から取得
        self.sf_function_name = os.environ.get('SF_API_FUNCTION_NAME')
        self.search_function_name = os.environ.get('WEB_SEARCH_FUNCTION_NAME')

        # Strands Agent for support assistance
        self.support_agent = self._initialize_support_agent()

    def process_support_request(self, case_id, question):
        """
        サポートリクエストを処理し、統合された回答を生成
        """
        try:
            # 1. ケースレコードの分析
            case_analysis = self.record_analyzer.analyze_case(case_id)

            # 2. 関連する外部情報の検索
            search_results = self.workflow_advisor.search_external_info(
                case_analysis.get('subject', ''),
                case_analysis.get('description', '')
            )

            # 3. Strands Agentによる統合回答の生成
            integrated_response = self._generate_integrated_response_with_strands(
                case_analysis, search_results, question
            )

            return {
                'case_analysis': case_analysis,
                'external_info': search_results,
                'ai_response': integrated_response,
                'recommendations': self._generate_recommendations(case_analysis, search_results)
            }

        except Exception as e:
            print(f"Integration error: {str(e)}")
            raise e

    def _initialize_support_agent(self):
        """
        Salesforceサポート専用のStrands Agentを初期化
        """
        # Salesforceサポートに特化したシステムプロンプト
        SUPPORT_SYSTEM_PROMPT = """
        あなたはSalesforceのカスタマーサポートエージェントです。以下の能力を持っています：

        1. ケース情報の分析と理解
        2. 類似ケースからの学習と解決パターンの識別
        3. 外部情報（既知問題、製品情報等）の統合
        4. 具体的で実行可能な解決手順の提示
        5. エスカレーション判断の支援
        6. 顧客への返信テンプレートの生成

        回答時の要件：
        - 日本語で回答
        - 具体的で実行可能な手順を提示
        - 必要に応じてエスカレーション基準を明示
        - 顧客に優しく、プロフェッショナルな対応を心がける
        - 類似ケースがあれば参考情報として活用
        """

        # カスタムツールの作成
        custom_tools = create_strands_tools(
            self.lambda_client,
            self.sf_function_name,
            self.search_function_name
        )

        # 利用可能なツールを設定
        tools = [custom_tools["salesforce_data"], custom_tools["web_search"], http_request, calculator, current_time , python_repl]

        return Agent(
            system_prompt=SUPPORT_SYSTEM_PROMPT,
            tools=tools
        )

    def _generate_integrated_response_with_strands(self, case_analysis, search_results, question):
        """
        Strands Agentを使用して統合された回答を生成
        """
        try:
            # プロンプトの構築
            context_prompt = f"""
            以下の情報を基に、顧客からの質問に対する適切なサポート回答を生成してください。

            ## ケース情報:
            - ケースID: {case_analysis.get('case_id', 'N/A')}
            - 件名: {case_analysis.get('subject', 'N/A')}
            - 説明: {case_analysis.get('description', 'N/A')}
            - 優先度: {case_analysis.get('priority', 'N/A')}
            - ステータス: {case_analysis.get('status', 'N/A')}
            - 顧客: {case_analysis.get('account_name', 'N/A')}
            - 製品: {case_analysis.get('product', 'N/A')}

            ## 類似ケース:
            {json.dumps(case_analysis.get('similar_cases', []), ensure_ascii=False, indent=2)}

            ## 外部検索結果:
            {json.dumps(search_results, ensure_ascii=False, indent=2)}

            ## 顧客からの質問:
            {question}

            この情報を統合して、具体的で実行可能な解決手順を含む回答を生成してください。
            """

            # Strands Agentで回答生成
            response = self.support_agent(context_prompt)

            return response

        except Exception as e:
            print(f"Strands Agent response generation error: {str(e)}")
            return "申し訳ございませんが、AIによる回答生成でエラーが発生しました。手動でのサポートをご提供いたします。"

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