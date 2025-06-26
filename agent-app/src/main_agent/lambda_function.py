import json
import os
import boto3
import logging
from agents.integration_manager import IntegrationManager

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
    メインエージェントのエントリーポイント
    """
    request_id = context.aws_request_id if context else 'local'
    logger.info(f"[{request_id}] Lambda function started")
    
    try:
        # イベント詳細をログ出力
        logger.info(f"[{request_id}] Received event keys: {list(event.keys())}")
        logger.debug(f"[{request_id}] Full event: {json.dumps(event, default=str)}")
        
        # CORS ヘッダー
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        logger.info(f"[{request_id}] CORS headers configured")

        # リクエストボディの解析
        if 'body' not in event:
            logger.error(f"[{request_id}] No body found in event")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'No body provided', 'request_id': request_id})
            }

        logger.info(f"[{request_id}] Body type: {type(event['body'])}")
        logger.debug(f"[{request_id}] Raw body content: {event['body']}")
        
        # JSONパース処理
        try:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            logger.info(f"[{request_id}] Successfully parsed body with keys: {list(body.keys())}")
            logger.debug(f"[{request_id}] Parsed body: {body}")
        except json.JSONDecodeError as e:
            logger.error(f"[{request_id}] JSON decode error: {str(e)}")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid JSON format', 'request_id': request_id})
            }

        # 必須パラメータのチェック
        required_params = ['case_id', 'question']
        missing_params = [param for param in required_params if param not in body]
        
        if missing_params:
            logger.error(f"[{request_id}] Missing required parameters: {missing_params}")
            logger.info(f"[{request_id}] Available parameters: {list(body.keys())}")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': f'Missing required parameters: {missing_params}',
                    'required': required_params,
                    'provided': list(body.keys()),
                    'request_id': request_id
                })
            }

        case_id = body['case_id']
        question = body['question']
        logger.info(f"[{request_id}] Processing request - Case ID: {case_id}, Question length: {len(question)} chars")
        logger.debug(f"[{request_id}] Question content: {question}")

        # 統合マネージャーの初期化
        logger.info(f"[{request_id}] Initializing IntegrationManager")
        integration_manager = IntegrationManager()
        logger.info(f"[{request_id}] IntegrationManager initialized successfully")

        # AIエージェントによる回答生成
        logger.info(f"[{request_id}] Starting support request processing")
        response = integration_manager.process_support_request(case_id, question)
        logger.info(f"[{request_id}] Support request processing completed")
        
        # レスポンス概要をログ出力
        response_keys = list(response.keys()) if isinstance(response, dict) else []
        logger.info(f"[{request_id}] Response generated with keys: {response_keys}")

        final_response = {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response, ensure_ascii=False)
        }
        
        logger.info(f"[{request_id}] Lambda function completed successfully")
        return final_response

    except Exception as e:
        logger.error(f"[{request_id}] Unhandled error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'request_id': request_id
            })
        }