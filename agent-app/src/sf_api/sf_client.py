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

        self.instance_url = os.environ.get("SALESFORCE_INSTANCE_URL")
        self.client_id = os.environ.get("SALESFORCE_CLIENT_ID")
        self.client_secret = os.environ.get("SALESFORCE_CLIENT_SECRET")

        logger.info(f"Instance URL: {self.instance_url}")
        logger.info(
            f"Client ID: {self.client_id[:10]}..."
            if self.client_id
            else "Client ID: None"
        )

        # Token management
        self.access_token = None
        self.token_expiry = None

        # API version
        self.api_version = "v63.0"
        logger.info(f"API Version: {self.api_version}")

    def _get_access_token(self):
        """
        OAuth 2.0 Client Credentials Flowを使用してアクセストークンを取得
        """
        # トークンが有効な場合は再利用
        if (
            self.access_token
            and self.token_expiry
            and datetime.now() < self.token_expiry
        ):
            return self.access_token

        # OAuth endpoint
        token_url = f"{self.instance_url}/services/oauth2/token"

        # Client Credentials Flow parameters
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(token_url, data=payload)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]

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
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.instance_url}/services/data/{self.api_version}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # 401の場合はトークンをリフレッシュして再試行
            if response.status_code == 401:
                self.access_token = None
                self.token_expiry = None
                access_token = self._get_access_token()
                headers["Authorization"] = f"Bearer {access_token}"

                if method == "GET":
                    response = requests.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json=data)
                elif method == "PATCH":
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

        result = self._make_api_request("GET", "/query", params={"q": query})
        logger.info(f"Query result: totalSize={result.get('totalSize', 0)}")

        if result["totalSize"] > 0:
            case_data = result["records"][0]
            logger.info(f"Case found - Subject: {case_data.get('Subject', 'N/A')}")
            return case_data
        else:
            logger.error(f"Case not found: {case_id}")
            raise Exception(f"Case not found: {case_id}")

    def find_similar_cases(self, subject):
        """
        類似ケースを検索（広範囲検索）
        取引先IDによる絞り込みを削除し、より広範囲な検索を実行
        """
        logger.info(f"Finding similar cases for subject: {subject}")

        # SOSLクエリで類似ケースを検索
        # subjectから重要なキーワードを抽出して検索
        search_terms = self._extract_search_keywords(subject)

        # 複数のキーワードを使った検索
        similar_cases = []

        for search_term in search_terms:
            escaped_term = search_term.replace("'", "\\'")
            sosl_query = f"FIND {{{escaped_term}}} IN ALL FIELDS RETURNING Case(Id, CaseNumber, Subject, Status, Priority, CreatedDate, Description)"

            # 基本的な絞り込み条件（クローズしたケースも含める）
            where_clauses = ["Id != NULL"]  # 基本的な有効性チェック

            where_clause = " WHERE " + " AND ".join(where_clauses)
            sosl_query = sosl_query.replace(
                ")", f"{where_clause} ORDER BY CreatedDate DESC LIMIT 15)"
            )

            logger.debug(f"SOSL Query: {sosl_query}")

            try:
                result = self._make_api_request(
                    "GET", "/search", params={"q": sosl_query}
                )

                # 検索結果からケース情報を抽出
                for record in result.get("searchRecords", []):
                    if record["attributes"]["type"] == "Case":
                        case_data = {
                            "Id": record["Id"],
                            "CaseNumber": record.get("CaseNumber"),
                            "Subject": record.get("Subject"),
                            "Status": record.get("Status"),
                            "Priority": record.get("Priority"),
                            "CreatedDate": record.get("CreatedDate"),
                            "Description": record.get("Description"),
                        }

                        # 重複を避けるため、IDでチェック
                        if not any(
                            case["Id"] == case_data["Id"] for case in similar_cases
                        ):
                            # 類似度を計算（簡単な文字列マッチング）
                            similarity = self._calculate_similarity(
                                subject, case_data["Subject"] or ""
                            )
                            case_data["similarity"] = similarity
                            similar_cases.append(case_data)

            except Exception as e:
                logger.warning(f"Search failed for term '{search_term}': {str(e)}")
                continue

        # 類似度でソートして上位10件を返す
        similar_cases.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        result_cases = similar_cases[:10]

        logger.info(f"Found {len(result_cases)} similar cases")
        return result_cases

    def _extract_search_keywords(self, subject):
        """
        件名から検索用キーワードを抽出
        """
        if not subject:
            return []

        # 基本的なキーワード抽出
        # 日本語の一般的な助詞・接続詞を除外
        stop_words = {
            "の",
            "が",
            "は",
            "を",
            "に",
            "で",
            "と",
            "から",
            "まで",
            "について",
            "による",
            "により",
        }

        # 単語を分割（簡易的な分割）
        words = []
        current_word = ""

        for char in subject:
            if char.isalnum() or char in "ー－":
                current_word += char
            else:
                if (
                    current_word
                    and len(current_word) >= 2
                    and current_word not in stop_words
                ):
                    words.append(current_word)
                current_word = ""

        if current_word and len(current_word) >= 2 and current_word not in stop_words:
            words.append(current_word)

        # 元の件名も含める
        keywords = [subject]
        if words:
            # 重要そうなキーワードを優先
            keywords.extend(words[:3])

        logger.debug(f"Extracted keywords: {keywords}")
        return keywords[:3]  # 最大3つのキーワードで検索

    def _calculate_similarity(self, text1, text2):
        """
        簡単な類似度計算（文字列の共通部分を基準）
        """
        if not text1 or not text2:
            return 0

        # 文字列を正規化
        text1 = text1.lower().replace(" ", "")
        text2 = text2.lower().replace(" ", "")

        # 共通文字数をカウント
        common_chars = 0
        text1_chars = list(text1)
        text2_chars = list(text2)

        for char in text1_chars:
            if char in text2_chars:
                common_chars += 1
                text2_chars.remove(char)  # 重複カウントを避ける

        # 類似度を計算（0-1の範囲）
        max_length = max(len(text1), len(text2))
        if max_length == 0:
            return 0

        similarity = common_chars / max_length
        return similarity

    def get_case_history(self, case_id):
        """
        ケースの履歴を取得
        """
        query = f"SELECT Id, Field, OldValue, NewValue, CreatedDate, CreatedBy.Name FROM CaseHistory WHERE CaseId = '{case_id}' ORDER BY CreatedDate DESC LIMIT 20"

        result = self._make_api_request("GET", "/query", params={"q": query})

        history = []
        for record in result.get("records", []):
            history.append(
                {
                    "Field": record.get("Field"),
                    "OldValue": record.get("OldValue"),
                    "NewValue": record.get("NewValue"),
                    "CreatedDate": record.get("CreatedDate"),
                    "CreatedBy": record.get("CreatedBy", {}).get("Name"),
                }
            )

        return history

    def update_case(self, case_id, updates):
        """
        ケースを更新
        """
        endpoint = f"/sobjects/Case/{case_id}"
        return self._make_api_request("PATCH", endpoint, data=updates)

    def add_case_comment(self, case_id, comment_body, is_public=False):
        """
        ケースにコメントを追加
        """
        comment_data = {
            "ParentId": case_id,
            "CommentBody": comment_body,
            "IsPublished": is_public,
        }

        endpoint = "/sobjects/CaseComment"
        return self._make_api_request("POST", endpoint, data=comment_data)
