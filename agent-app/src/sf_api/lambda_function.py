import json
import logging
from sf_client import SalesforceClient

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
    Salesforce API アクセス用のLambda関数
    """
    request_id = context.aws_request_id if context else 'local'
    logger.info(f"[{request_id}] SF API Lambda function started")
    
    try:
        # イベントの詳細をログ出力
        logger.info(f"[{request_id}] Received event keys: {list(event.keys())}")
        logger.debug(f"[{request_id}] Full event: {json.dumps(event, default=str)}")
        
        # Salesforceクライアントの初期化
        logger.info(f"[{request_id}] Initializing Salesforce client")
        sf_client = SalesforceClient()
        logger.info(f"[{request_id}] Salesforce client initialized successfully")

        # アクションに応じて処理を分岐
        action = event.get('action')
        logger.info(f"[{request_id}] Processing action: {action}")

        if action == 'get_case':
            case_id = event.get('case_id')
            logger.info(f"[{request_id}] Get case action - Case ID: {case_id}")
            
            if not case_id:
                logger.error(f"[{request_id}] Missing case_id parameter")
                raise ValueError('case_id is required')

            logger.info(f"[{request_id}] Calling Salesforce API to get case data")
            case_data = sf_client.get_case(case_id)
            logger.info(f"[{request_id}] Case data retrieved successfully. Subject: {case_data.get('Subject', 'N/A')}")
            
            return {
                'statusCode': 200,
                'case_data': case_data
            }

        elif action == 'find_similar_cases':
            subject = event.get('subject', '')
            product = event.get('product', '')
            account_id = event.get('account_id', '')
            logger.info(f"[{request_id}] Find similar cases - Subject: {subject}, Product: {product}, Account: {account_id}")

            logger.info(f"[{request_id}] Calling Salesforce API to find similar cases")
            similar_cases = sf_client.find_similar_cases(subject, product, account_id)
            logger.info(f"[{request_id}] Found {len(similar_cases)} similar cases")
            
            return {
                'statusCode': 200,
                'similar_cases': similar_cases
            }

        elif action == 'get_case_history':
            case_id = event.get('case_id')
            logger.info(f"[{request_id}] Get case history - Case ID: {case_id}")
            
            if not case_id:
                logger.error(f"[{request_id}] Missing case_id parameter")
                raise ValueError('case_id is required')

            logger.info(f"[{request_id}] Calling Salesforce API to get case history")
            case_history = sf_client.get_case_history(case_id)
            logger.info(f"[{request_id}] Retrieved {len(case_history)} history records")
            
            return {
                'statusCode': 200,
                'case_history': case_history
            }

        else:
            logger.error(f"[{request_id}] Unknown action: {action}")
            raise ValueError(f'Unknown action: {action}')

    except Exception as e:
        logger.error(f"[{request_id}] SF API Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'errorMessage': str(e)
        }