"""
Strands Agents用のカスタムツール定義
"""
import json
import boto3
from typing import Dict, Any, List

class SalesforceDataTool:
    """
    Salesforceデータにアクセスするためのカスタムツール
    """

    def __init__(self, lambda_client):
        self.lambda_client = lambda_client
        self.sf_function_name = None

    def set_sf_function_name(self, function_name):
        self.sf_function_name = function_name

    def get_case_details(self, case_id: str) -> Dict[str, Any]:
        """
        指定されたケースIDの詳細情報を取得
        """
        try:
            payload = {
                'action': 'get_case',
                'case_id': case_id
            }

            response = self.lambda_client.invoke(
                FunctionName=self.sf_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            result = json.loads(response['Payload'].read())
            return result.get('case_data', {})

        except Exception as e:
            return {'error': f'ケースデータの取得に失敗しました: {str(e)}'}

    def find_similar_cases(self, subject: str, product: str = '', account_id: str = '') -> List[Dict]:
        """
        類似ケースを検索
        """
        try:
            payload = {
                'action': 'find_similar_cases',
                'subject': subject,
                'product': product,
                'account_id': account_id
            }

            response = self.lambda_client.invoke(
                FunctionName=self.sf_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            result = json.loads(response['Payload'].read())
            return result.get('similar_cases', [])

        except Exception as e:
            return [{'error': f'類似ケースの検索に失敗しました: {str(e)}'}]

class WebSearchTool:
    """
    Web検索を行うためのカスタムツール
    """

    def __init__(self, lambda_client):
        self.lambda_client = lambda_client
        self.search_function_name = None

    def set_search_function_name(self, function_name):
        self.search_function_name = function_name

    def search_knowledge_base(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        外部ナレッジベースを検索
        """
        try:
            payload = {
                'query': query,
                'max_results': max_results
            }

            response = self.lambda_client.invoke(
                FunctionName=self.search_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            result = json.loads(response['Payload'].read())
            return result.get('search_results', {})

        except Exception as e:
            return {'error': f'外部検索に失敗しました: {str(e)}'}

def create_strands_tools(lambda_client, sf_function_name, search_function_name):
    """
    Strands Agents用のツールセットを作成
    """
    sf_tool = SalesforceDataTool(lambda_client)
    sf_tool.set_sf_function_name(sf_function_name)

    search_tool = WebSearchTool(lambda_client)
    search_tool.set_search_function_name(search_function_name)

    # Strands Agent用のツール定義を返す
    return {
        'salesforce_data': sf_tool,
        'web_search': search_tool
    }