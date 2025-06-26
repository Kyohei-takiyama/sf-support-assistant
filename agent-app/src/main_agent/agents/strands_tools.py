"""
Strands Agents用のカスタムツール定義
"""
import json
import os
import boto3
from typing import Dict, Any, List

# Lambda クライアントをグローバルに初期化
lambda_client = boto3.client('lambda')

def get_salesforce_case_details(case_id: str) -> Dict[str, Any]:
    """
    指定されたケースIDの詳細情報を取得
    
    Args:
        case_id (str): Salesforce ケースID
        
    Returns:
        Dict[str, Any]: ケースの詳細情報
    """
    try:
        sf_function_name = os.environ.get('SF_API_FUNCTION_NAME')
        payload = {
            'action': 'get_case',
            'case_id': case_id
        }

        response = lambda_client.invoke(
            FunctionName=sf_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        result = json.loads(response['Payload'].read())
        return result.get('case_data', {})

    except Exception as e:
        return {'error': f'ケースデータの取得に失敗しました: {str(e)}'}

def find_similar_salesforce_cases(subject: str, product: str = '', account_id: str = '') -> List[Dict]:
    """
    類似ケースを検索
    
    Args:
        subject (str): ケースの件名
        product (str): 製品名（オプション）
        account_id (str): アカウントID（オプション）
        
    Returns:
        List[Dict]: 類似ケースのリスト
    """
    try:
        sf_function_name = os.environ.get('SF_API_FUNCTION_NAME')
        payload = {
            'action': 'find_similar_cases',
            'subject': subject,
            'product': product,
            'account_id': account_id
        }

        response = lambda_client.invoke(
            FunctionName=sf_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        result = json.loads(response['Payload'].read())
        return result.get('similar_cases', [])

    except Exception as e:
        return [{'error': f'類似ケースの検索に失敗しました: {str(e)}'}]

def search_external_knowledge(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    外部ナレッジベースを検索
    
    Args:
        query (str): 検索クエリ
        max_results (int): 最大結果数
        
    Returns:
        Dict[str, Any]: 検索結果
    """
    try:
        search_function_name = os.environ.get('WEB_SEARCH_FUNCTION_NAME')
        payload = {
            'query': query,
            'max_results': max_results
        }

        response = lambda_client.invoke(
            FunctionName=search_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        result = json.loads(response['Payload'].read())
        return result.get('search_results', {})

    except Exception as e:
        return {'error': f'外部検索に失敗しました: {str(e)}'}