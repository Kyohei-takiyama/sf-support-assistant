import json
from tavily_client import TavilyClient

def lambda_handler(event, context):
    """
    Web検索（Tavily API）用のLambda関数
    """
    try:
        # Tavilyクライアントの初期化
        tavily_client = TavilyClient()

        # 検索パラメータの取得
        query = event.get('query')
        if not query:
            raise ValueError('query is required')

        max_results = event.get('max_results', 5)

        # Web検索の実行
        search_results = tavily_client.search(query, max_results)

        return {
            'statusCode': 200,
            'search_results': search_results,
            'query': query
        }

    except Exception as e:
        print(f"Web search error: {str(e)}")
        return {
            'statusCode': 500,
            'errorMessage': str(e)
        }