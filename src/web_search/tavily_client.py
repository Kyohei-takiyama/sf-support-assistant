import os
import requests

class TavilyClient:
    """
    Tavily API クライアント
    """

    def __init__(self):
        """
        環境変数からAPIキーを取得して初期化
        """
        self.api_key = os.environ.get('TAVILY_API_KEY')
        if not self.api_key:
            raise ValueError('TAVILY_API_KEY environment variable is required')

        self.base_url = 'https://api.tavily.com'

    def search(self, query, max_results=5):
        """
        Web検索を実行
        """
        try:
            url = f"{self.base_url}/search"

            payload = {
                'api_key': self.api_key,
                'query': query,
                'search_depth': 'basic',  # 'basic' or 'advanced'
                'include_answer': True,
                'include_raw_content': False,
                'max_results': max_results,
                'include_domains': [],
                'exclude_domains': []
            }

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # レスポンスを整形
            formatted_results = []

            if 'results' in data:
                for result in data['results']:
                    formatted_result = {
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'content': result.get('content', ''),
                        'score': result.get('score', 0)
                    }
                    formatted_results.append(formatted_result)

            return {
                'results': formatted_results,
                'answer': data.get('answer', ''),
                'query': query,
                'response_time': data.get('response_time', 0)
            }

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            raise e
        except Exception as e:
            print(f"Tavily search error: {str(e)}")
            raise e