import json
import os

class RecordAnalyzer:
    """
    Salesforceレコードを分析するエージェント
    """

    def __init__(self, lambda_client):
        self.lambda_client = lambda_client
        self.sf_function_name = os.environ.get('SF_API_FUNCTION_NAME')

    def analyze_case(self, case_id):
        """
        ケースレコードを分析し、関連情報を取得
        """
        try:
            # Salesforce API Lambda を呼び出してケース情報を取得
            case_data = self._get_case_data(case_id)

            # 関連ケースの検索
            similar_cases = self._find_similar_cases(case_data)

            # 分析結果をまとめる
            analysis = {
                'case_id': case_id,
                'subject': case_data.get('Subject', ''),
                'description': case_data.get('Description', ''),
                'priority': case_data.get('Priority', ''),
                'status': case_data.get('Status', ''),
                'account_name': case_data.get('Account', {}).get('Name', ''),
                'contact_name': case_data.get('Contact', {}).get('Name', ''),
                'product': case_data.get('Product__c', ''),
                'similar_cases': similar_cases,
                'case_history': self._get_case_history(case_id)
            }

            return analysis

        except Exception as e:
            print(f"Case analysis error: {str(e)}")
            return {
                'case_id': case_id,
                'error': f'ケース分析でエラーが発生しました: {str(e)}'
            }

    def _get_case_data(self, case_id):
        """
        Salesforce API Lambdaを呼び出してケースデータを取得
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
            if 'errorMessage' in result:
                raise Exception(result['errorMessage'])

            return result.get('case_data', {})

        except Exception as e:
            print(f"Error getting case data: {str(e)}")
            raise e

    def _find_similar_cases(self, case_data):
        """
        類似ケースを検索
        """
        try:
            payload = {
                'action': 'find_similar_cases',
                'subject': case_data.get('Subject', ''),
                'product': case_data.get('Product__c', ''),
                'account_id': case_data.get('AccountId', '')
            }

            response = self.lambda_client.invoke(
                FunctionName=self.sf_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            result = json.loads(response['Payload'].read())
            return result.get('similar_cases', [])

        except Exception as e:
            print(f"Error finding similar cases: {str(e)}")
            return []

    def _get_case_history(self, case_id):
        """
        ケースの履歴を取得
        """
        try:
            payload = {
                'action': 'get_case_history',
                'case_id': case_id
            }

            response = self.lambda_client.invoke(
                FunctionName=self.sf_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            result = json.loads(response['Payload'].read())
            return result.get('case_history', [])

        except Exception as e:
            print(f"Error getting case history: {str(e)}")
            return []