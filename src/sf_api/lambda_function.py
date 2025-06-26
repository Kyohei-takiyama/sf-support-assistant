import json
from sf_client import SalesforceClient

def lambda_handler(event, context):
    """
    Salesforce API アクセス用のLambda関数
    """
    try:
        # Salesforceクライアントの初期化
        sf_client = SalesforceClient()

        # アクションに応じて処理を分岐
        action = event.get('action')

        if action == 'get_case':
            case_id = event.get('case_id')
            if not case_id:
                raise ValueError('case_id is required')

            case_data = sf_client.get_case(case_id)
            return {
                'statusCode': 200,
                'case_data': case_data
            }

        elif action == 'find_similar_cases':
            subject = event.get('subject', '')
            product = event.get('product', '')
            account_id = event.get('account_id', '')

            similar_cases = sf_client.find_similar_cases(subject, product, account_id)
            return {
                'statusCode': 200,
                'similar_cases': similar_cases
            }

        elif action == 'get_case_history':
            case_id = event.get('case_id')
            if not case_id:
                raise ValueError('case_id is required')

            case_history = sf_client.get_case_history(case_id)
            return {
                'statusCode': 200,
                'case_history': case_history
            }

        else:
            raise ValueError(f'Unknown action: {action}')

    except Exception as e:
        print(f"SF API Error: {str(e)}")
        return {
            'statusCode': 500,
            'errorMessage': str(e)
        }