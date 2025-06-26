import json
import os
import logging

# ログ設定
logger = logging.getLogger(__name__)

class RecordAnalyzer:
    """
    Salesforceレコードを分析するエージェント
    """

    def __init__(self, lambda_client):
        logger.info("Initializing RecordAnalyzer")
        self.lambda_client = lambda_client
        self.sf_function_name = os.environ.get('SF_API_FUNCTION_NAME')
        logger.info(f"SF Function Name: {self.sf_function_name}")

    def analyze_case(self, case_id):
        """
        ケースレコードを分析し、関連情報を取得
        """
        logger.info(f"Starting case analysis for case ID: {case_id}")
        
        try:
            # Salesforce API Lambda を呼び出してケース情報を取得
            logger.info("Fetching case data from Salesforce")
            case_data = self._get_case_data(case_id)
            
            if not case_data:
                logger.error("No case data received from Salesforce API")
                return {'case_id': case_id, 'error': 'Case not found or access denied'}
            
            logger.info(f"Case data retrieved successfully. Subject: {case_data.get('Subject', 'N/A')}")

            # 関連ケースの検索
            logger.info("Searching for similar cases")
            similar_cases = self._find_similar_cases(case_data)
            logger.info(f"Found {len(similar_cases)} similar cases")

            # 分析結果をまとめる
            logger.info("Assembling case analysis results")
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

            logger.info("Case analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Case analysis error: {str(e)}", exc_info=True)
            return {
                'case_id': case_id,
                'error': f'ケース分析でエラーが発生しました: {str(e)}'
            }

    def _get_case_data(self, case_id):
        """
        Salesforce API Lambdaを呼び出してケースデータを取得
        """
        logger.debug(f"Getting case data for case ID: {case_id}")
        
        try:
            payload = {
                'action': 'get_case',
                'case_id': case_id
            }
            logger.debug(f"Calling SF API Lambda with payload: {payload}")

            response = self.lambda_client.invoke(
                FunctionName=self.sf_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            logger.debug("SF API Lambda call completed")

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