import os
import json
import requests
from datetime import datetime, timedelta


class SalesforceClient:
    """
    Salesforce API Client using OAuth 2.0 Client Credentials Flow
    """

    def __init__(self):
        self.instance_url = os.environ.get('SALESFORCE_INSTANCE_URL')
        self.client_id = os.environ.get('SALESFORCE_CLIENT_ID')
        self.client_secret = os.environ.get('SALESFORCE_CLIENT_SECRET')

        # Token management
        self.access_token = None
        self.token_expiry = None

        # API version
        self.api_version = 'v63.0'

    def _get_access_token(self):
        """
        OAuth 2.0 Client Credentials Flowを使用してアクセストークンを取得
        """
        # トークンが有効な場合は再利用
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        # OAuth endpoint
        token_url = f"{self.instance_url}/services/oauth2/token"

        # Client Credentials Flow parameters
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        try:
            response = requests.post(token_url, data=payload)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']

            # トークンの有効期限を設定（デフォルトは2時間、安全のため1時間50分で設定）
            self.token_expiry = datetime.now() + timedelta(hours=1, minutes=50)

            return self.access_token

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to obtain access token: {str(e)}")

    def _make_api_request(self, method, endpoint, data=None, params=None):
        """
        Salesforce APIへのリクエストを実行
        """
        access_token = self._get_access_token()

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        url = f"{self.instance_url}/services/data/{self.api_version}{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # 401の場合はトークンをリフレッシュして再試行
            if response.status_code == 401:
                self.access_token = None
                self.token_expiry = None
                access_token = self._get_access_token()
                headers['Authorization'] = f'Bearer {access_token}'

                if method == 'GET':
                    response = requests.get(url, headers=headers, params=params)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=data)
                elif method == 'PATCH':
                    response = requests.patch(url, headers=headers, json=data)

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def get_case(self, case_id):
        """
        ケースレコードの詳細情報を取得
        """
        try:
            # ケース情報を取得（関連するアカウント、コンタクト情報も含む）
            query = f"""
            SELECT Id, CaseNumber, Subject, Description, Status, Priority,
                   Account.Name, Contact.Name, Product__c, CreatedDate,
                   LastModifiedDate, Origin, Type
            FROM Case
            WHERE Id = '{case_id}'
            """

            result = self.sf.query(query)

            if result['totalSize'] == 0:
                raise ValueError(f'Case not found: {case_id}')

            return result['records'][0]

        except Exception as e:
            print(f"Error getting case: {str(e)}")
            raise e

    def find_similar_cases(self, subject, product='', account_id='', limit=5):
        """
        類似ケースを検索
        """
        try:
            # 基本的な検索条件
            where_conditions = []
            where_conditions.append("Status = 'Closed'")  # 解決済みケースのみ

            # 件名に含まれるキーワードで検索（簡易版）
            if subject:
                keywords = subject.split()[:3]  # 最初の3つのキーワード
                for keyword in keywords:
                    if len(keyword) > 2:
                        where_conditions.append(f"Subject LIKE '%{keyword}%'")

            # 製品が同じケース
            if product:
                where_conditions.append(f"Product__c = '{product}'")

            # 同じアカウントのケース
            if account_id:
                where_conditions.append(f"AccountId = '{account_id}'")

            where_clause = " AND ".join(where_conditions)

            query = f"""
            SELECT Id, CaseNumber, Subject, Status, Priority,
                   Resolution__c, CreatedDate, ClosedDate
            FROM Case
            WHERE {where_clause}
            ORDER BY ClosedDate DESC
            LIMIT {limit}
            """

            result = self.sf.query(query)
            return result['records']

        except Exception as e:
            print(f"Error finding similar cases: {str(e)}")
            return []

    def get_case_history(self, case_id, limit=10):
        """
        ケースの履歴（活動履歴、コメント等）を取得
        """
        try:
            # ケースコメントを取得
            comment_query = f"""
            SELECT Id, CommentBody, CreatedBy.Name, CreatedDate, IsPublished
            FROM CaseComment
            WHERE ParentId = '{case_id}'
            ORDER BY CreatedDate DESC
            LIMIT {limit}
            """

            comments = self.sf.query(comment_query)

            # ケース履歴（フィールド変更履歴）を取得
            history_query = f"""
            SELECT Id, Field, OldValue, NewValue, CreatedBy.Name, CreatedDate
            FROM CaseHistory
            WHERE CaseId = '{case_id}'
            ORDER BY CreatedDate DESC
            LIMIT {limit}
            """

            history = self.sf.query(history_query)

            return {
                'comments': comments['records'],
                'field_history': history['records']
            }

        except Exception as e:
            print(f"Error getting case history: {str(e)}")
            return {
                'comments': [],
                'field_history': []
            }