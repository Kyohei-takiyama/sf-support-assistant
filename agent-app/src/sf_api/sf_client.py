import os
import json
import requests
import logging
from datetime import datetime, timedelta

# ログ設定
logger = logging.getLogger(__name__)

class SalesforceClient:
    """
    Salesforce API Client using OAuth 2.0 Client Credentials Flow
    """
    
    def __init__(self):
        logger.info("Initializing Salesforce client")
        
        self.instance_url = os.environ.get('SALESFORCE_INSTANCE_URL')
        self.client_id = os.environ.get('SALESFORCE_CLIENT_ID')
        self.client_secret = os.environ.get('SALESFORCE_CLIENT_SECRET')
        
        logger.info(f"Instance URL: {self.instance_url}")
        logger.info(f"Client ID: {self.client_id[:10]}..." if self.client_id else "Client ID: None")
        
        # Token management
        self.access_token = None
        self.token_expiry = None
        
        # API version
        self.api_version = 'v63.0'
        logger.info(f"API Version: {self.api_version}")
        
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
        ケース情報を取得
        """
        logger.info(f"Getting case data for case ID: {case_id}")
        
        query = f"SELECT Id, CaseNumber, Subject, Description, Status, Priority, Account.Name, Contact.Name, CreatedDate, LastModifiedDate, Owner.Name FROM Case WHERE Id = '{case_id}'"
        logger.debug(f"SOQL Query: {query}")
        
        result = self._make_api_request('GET', '/query', params={'q': query})
        logger.info(f"Query result: totalSize={result.get('totalSize', 0)}")
        
        if result['totalSize'] > 0:
            case_data = result['records'][0]
            logger.info(f"Case found - Subject: {case_data.get('Subject', 'N/A')}")
            return case_data
        else:
            logger.error(f"Case not found: {case_id}")
            raise Exception(f"Case not found: {case_id}")
    
    def find_similar_cases(self, subject, product=None, account_id=None):
        """
        類似ケースを検索
        """
        # SOSLクエリで類似ケースを検索
        search_term = subject.replace("'", "\\'")
        sosl_query = f"FIND {{{search_term}}} IN ALL FIELDS RETURNING Case(Id, CaseNumber, Subject, Status)"
        
        # 追加の絞り込み条件
        where_clauses = []
        if account_id:
            where_clauses.append(f"AccountId = '{account_id}'")
            
        if where_clauses:
            where_clause = " WHERE " + " AND ".join(where_clauses)
            sosl_query = sosl_query.replace(")", f"{where_clause} LIMIT 10)")
        else:
            sosl_query = sosl_query.replace(")", " LIMIT 10)")
            
        result = self._make_api_request('GET', '/search', params={'q': sosl_query})
        
        # 検索結果からケース情報を抽出
        similar_cases = []
        for record in result.get('searchRecords', []):
            if record['attributes']['type'] == 'Case':
                similar_cases.append({
                    'Id': record['Id'],
                    'CaseNumber': record.get('CaseNumber'),
                    'Subject': record.get('Subject'),
                    'Status': record.get('Status')
                })
                
        return similar_cases
    
    def get_case_history(self, case_id):
        """
        ケースの履歴を取得
        """
        query = f"SELECT Id, Field, OldValue, NewValue, CreatedDate, CreatedBy.Name FROM CaseHistory WHERE CaseId = '{case_id}' ORDER BY CreatedDate DESC LIMIT 20"
        
        result = self._make_api_request('GET', '/query', params={'q': query})
        
        history = []
        for record in result.get('records', []):
            history.append({
                'Field': record.get('Field'),
                'OldValue': record.get('OldValue'),
                'NewValue': record.get('NewValue'),
                'CreatedDate': record.get('CreatedDate'),
                'CreatedBy': record.get('CreatedBy', {}).get('Name')
            })
            
        return history
    
    def update_case(self, case_id, updates):
        """
        ケースを更新
        """
        endpoint = f"/sobjects/Case/{case_id}"
        return self._make_api_request('PATCH', endpoint, data=updates)
    
    def add_case_comment(self, case_id, comment_body, is_public=False):
        """
        ケースにコメントを追加
        """
        comment_data = {
            'ParentId': case_id,
            'CommentBody': comment_body,
            'IsPublished': is_public
        }
        
        endpoint = "/sobjects/CaseComment"
        return self._make_api_request('POST', endpoint, data=comment_data)