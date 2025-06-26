import json
import logging
from tavily_client import TavilyClient

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ログフォーマット設定
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
if len(logger.handlers) == 0:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)

def lambda_handler(event, context):
    """
    Web検索（Tavily API）用のLambda関数
    """
    request_id = context.aws_request_id if context else 'local'
    logger.info(f"[{request_id}] Web Search Lambda function started")
    
    try:
        # イベントの詳細をログ出力
        logger.info(f"[{request_id}] Received event keys: {list(event.keys())}")
        logger.debug(f"[{request_id}] Full event: {json.dumps(event, default=str)}")
        
        # Tavilyクライアントの初期化
        logger.info(f"[{request_id}] Initializing Tavily client")
        tavily_client = TavilyClient()
        logger.info(f"[{request_id}] Tavily client initialized successfully")

        # 検索パラメータの取得
        query = event.get('query')
        if not query:
            logger.error(f"[{request_id}] Missing required parameter: query")
            raise ValueError('query is required')

        max_results = event.get('max_results', 5)
        logger.info(f"[{request_id}] Search parameters - Query: '{query}', Max results: {max_results}")

        # Web検索の実行
        logger.info(f"[{request_id}] Executing web search via Tavily API")
        search_results = tavily_client.search(query, max_results)
        
        # 検索結果の概要をログ出力
        result_count = len(search_results.get('results', []))
        logger.info(f"[{request_id}] Search completed - Found {result_count} results")
        logger.debug(f"[{request_id}] Search response time: {search_results.get('response_time', 'N/A')}s")

        response = {
            'statusCode': 200,
            'search_results': search_results,
            'query': query
        }
        
        logger.info(f"[{request_id}] Web Search Lambda function completed successfully")
        return response

    except Exception as e:
        logger.error(f"[{request_id}] Web search error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'errorMessage': str(e),
            'request_id': request_id
        }