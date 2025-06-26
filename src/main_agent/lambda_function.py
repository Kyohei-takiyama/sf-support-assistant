import json
import os
import boto3
from agents.integration_manager import IntegrationManager

def lambda_handler(event, context):
    """
    メインエージェントのエントリーポイント
    """
    try:
        # CORS ヘッダー
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }

        # リクエストボディの解析
        if 'body' not in event:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'No body provided'})
            }

        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']

        # 必須パラメータのチェック
        if 'case_id' not in body or 'question' not in body:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'case_id and question are required'})
            }

        case_id = body['case_id']
        question = body['question']

        # 統合マネージャーの初期化
        integration_manager = IntegrationManager()

        # AIエージェントによる回答生成
        response = integration_manager.process_support_request(case_id, question)

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }