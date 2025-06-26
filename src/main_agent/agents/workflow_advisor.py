import json
import os

class WorkflowAdvisor:
    """
    ワークフローの提案と外部情報検索を行うエージェント
    """

    def __init__(self, lambda_client):
        self.lambda_client = lambda_client
        self.search_function_name = os.environ.get('WEB_SEARCH_FUNCTION_NAME')

    def search_external_info(self, subject, description):
        """
        外部情報を検索してサポートに役立つ情報を取得
        """
        try:
            # 検索クエリの生成
            search_query = self._generate_search_query(subject, description)

            # Web検索の実行
            search_results = self._perform_web_search(search_query)

            return {
                'search_query': search_query,
                'results': search_results
            }

        except Exception as e:
            print(f"External info search error: {str(e)}")
            return {
                'error': f'外部情報検索でエラーが発生しました: {str(e)}'
            }

    def _generate_search_query(self, subject, description):
        """
        ケース情報から適切な検索クエリを生成
        """
        # シンプルな検索クエリ生成
        # 実際のプロダクトでは、より洗練されたクエリ生成ロジックを実装
        query_parts = []

        if subject:
            # 件名から重要なキーワードを抽出（簡易版）
            subject_keywords = [word for word in subject.split() if len(word) > 2]
            query_parts.extend(subject_keywords[:3])  # 最初の3つのキーワード

        if description:
            # 説明文から重要なキーワードを抽出（簡易版）
            desc_keywords = [word for word in description.split() if len(word) > 3]
            query_parts.extend(desc_keywords[:2])  # 最初の2つのキーワード

        # エラー関連のキーワードを追加
        query_parts.append("既知問題")
        query_parts.append("解決方法")

        return " ".join(query_parts[:5])  # 最大5つのキーワード

    def _perform_web_search(self, query):
        """
        Web検索Lambda関数を呼び出して外部情報を検索
        """
        try:
            payload = {
                'query': query,
                'max_results': 5
            }

            response = self.lambda_client.invoke(
                FunctionName=self.search_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            result = json.loads(response['Payload'].read())
            if 'errorMessage' in result:
                raise Exception(result['errorMessage'])

            return result.get('search_results', [])

        except Exception as e:
            print(f"Error performing web search: {str(e)}")
            return []

    def generate_workflow_recommendations(self, case_analysis, search_results):
        """
        ケース分析と外部情報に基づいてワークフローの推奨事項を生成
        """
        recommendations = []

        # 優先度に基づく推奨
        priority = case_analysis.get('priority', '').lower()
        if priority == 'high':
            recommendations.append({
                'type': 'immediate_action',
                'description': '高優先度ケースです。1時間以内に初回対応を行ってください。',
                'action': 'set_reminder'
            })

        # 類似ケースに基づく推奨
        similar_cases = case_analysis.get('similar_cases', [])
        if similar_cases:
            recommendations.append({
                'type': 'reference_cases',
                'description': f'{len(similar_cases)}件の類似ケースが見つかりました。解決パターンを参考にしてください。',
                'action': 'review_similar_cases'
            })

        # 外部情報に基づく推奨
        if search_results:
            recommendations.append({
                'type': 'external_research',
                'description': '関連する既知問題や解決方法が見つかりました。詳細を確認してください。',
                'action': 'review_external_info'
            })

        return recommendations