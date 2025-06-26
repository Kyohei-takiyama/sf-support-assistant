import os
import requests
import logging

# ログ設定
logger = logging.getLogger(__name__)

class TavilyClient:
    """
    Tavily API クライアント
    """

    def __init__(self):
        """
        環境変数からAPIキーを取得して初期化
        """
        logger.info("Initializing Tavily client")

        self.api_key = os.environ.get('TAVILY_API_KEY')
        if not self.api_key:
            logger.error("TAVILY_API_KEY environment variable not found")
            raise ValueError('TAVILY_API_KEY environment variable is required')

        logger.info(f"API Key configured (length: {len(self.api_key)} chars)")
        self.base_url = 'https://api.tavily.com'
        logger.info(f"Base URL: {self.base_url}")

    def search(self, query, max_results=5):
        """
        Web検索を実行
        """
        logger.info(f"Starting search - Query: '{query}', Max results: {max_results}")

        try:
            url = f"{self.base_url}/search"
            logger.debug(f"API URL: {url}")

            payload = {
                'api_key': self.api_key,
                'query': query,
                'search_depth': 'basic',  # 'basic' or 'advanced'
                'include_answer': True,
                'include_raw_content': False,
                'max_results': max_results,
                'include_domains': [],
                'exclude_domains': [],
                'include_images': True,
                'include_image_descriptions': True
            }

            logger.debug(f"Search payload (excluding API key): {{'query': '{query}', 'max_results': {max_results}, 'search_depth': 'basic', 'include_images': True}}")

            headers = {
                'Content-Type': 'application/json'
            }

            logger.info("Sending request to Tavily API")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            logger.info(f"Tavily API response status: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            logger.info(f"Received {len(data.get('results', []))} search results")
            logger.info(f"Received {len(data.get('images', []))} images")
            logger.debug(f"Response time: {data.get('response_time', 'N/A')}s")

            # レスポンスを整形
            formatted_results = []

            if 'results' in data:
                for i, result in enumerate(data['results']):
                    formatted_result = {
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'content': result.get('content', ''),
                        'score': result.get('score', 0)
                    }
                    formatted_results.append(formatted_result)
                    logger.debug(f"Result {i+1}: {result.get('title', 'No title')} (Score: {result.get('score', 0)})")

            search_response = {
                'results': formatted_results,
                'answer': data.get('answer', ''),
                'images': data.get('images', []),
                'query': query,
                'response_time': data.get('response_time', 0)
            }

            logger.info(f"Search completed successfully - Formatted {len(formatted_results)} results")
            if data.get('answer'):
                logger.info(f"AI-generated answer length: {len(data.get('answer', ''))} chars")
            if data.get('images'):
                logger.info(f"Images included: {len(data.get('images', []))} images")

            return search_response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}", exc_info=True)
            raise e
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}", exc_info=True)
            raise e