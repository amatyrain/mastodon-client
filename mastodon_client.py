import json as jsonlib
import requests
import inspect
import time


class MastodonClient:
    def __init__(self, base_uri, access_token):
        self.base_uri = base_uri
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
            "Accept": "application/json",
        }

    def _request(
        self,
        url: str,
        method: str,
        headers: dict | None = None,
        params=None,
        json: dict | None = None,
        files=None,
        expect_json: bool = True,
        retries: int = 3,
        timeout: int = 10,
    ):
        if headers is None:
            headers = self.headers

        print(f"url: {url}")
        print(f"method: {method}")
        print(f"json: {json}")
        print(f"params: {params}")

        attempt = 0
        response = None
        last_exc: Exception | None = None
        while attempt < retries:
            try:
                response = requests.request(
                    url=url,
                    method=method,
                    headers=headers,
                    json=json,
                    params=params,
                    files=files,
                    timeout=timeout,
                )
            except requests.exceptions.RequestException as e:
                last_exc = e
                attempt += 1
                if attempt < retries:
                    # ネットワークエラーの場合は2秒から開始して指数バックオフ
                    backoff = 2 ** attempt
                    print(f"Transient error on request ({e}), retrying in {backoff}s...")
                    time.sleep(backoff)
                    continue
                else:
                    raise Exception(f"Request failed after {retries} attempts: {e}")
            # if we got a response, check status
            if response is not None and response.status_code >= 500:
                # transient server error (500, 502, 503, etc.); retry
                attempt += 1
                if attempt < retries:
                    # 503エラーは特に長く待つ（サーバー過負荷対策）
                    if response.status_code == 503:
                        backoff = 2 ** (attempt + 1)  # より長いバックオフ
                    else:
                        backoff = 2 ** attempt
                    print(f"Server error {response.status_code} "
                          f"(retry {attempt}/{retries}) waiting {backoff}s...")
                    time.sleep(backoff)
                    continue
                # no more retries, will fall through to error handling below
                print(f"Server error {response.status_code} "
                      f"persisted after {retries} attempts")
            break

        # Try to parse JSON safely; fall back to text without raising JSONDecodeError
        return_response = None
        content_type = response.headers.get("Content-Type", "") if hasattr(response, "headers") else ""
        parsed_json = None
        if expect_json or ("json" in content_type.lower()):
            try:
                parsed_json = response.json()
            except Exception:
                parsed_json = None
        return_response = parsed_json if parsed_json is not None else response.text

        if response.status_code >= 400:
            # Build a helpful error with status, method, url and a small body preview
            body_preview = return_response
            if isinstance(body_preview, (dict, list)):
                try:
                    body_preview = jsonlib.dumps(body_preview)
                except Exception:
                    body_preview = str(body_preview)
            if isinstance(body_preview, str) and len(body_preview) > 500:
                body_preview = body_preview[:500] + "..."
            err_msg = (
                f"HTTP {response.status_code} for {method} {url}; "
                f"params={params} json={json}; body={body_preview}"
            )
            print(f"Error: {err_msg}")
            raise Exception(err_msg)

        return return_response

    def post(
        self,
        visibility: str,
        text: str,
        media_ids: list = [],
        sensitive: bool = False,
        spoiler_text: str | None = None,
    ) -> dict:
        current_frame = inspect.currentframe()
        method_name = (
            current_frame.f_code.co_name if current_frame else "unknown_method"
        )
        print(f"【start】{self.__class__.__name__}::{method_name}")

        method = "POST"
        endpoint = "/api/v1/statuses"
        url = f"{self.base_uri}{endpoint}"
        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
            "Content-Type": "application/json",
        }
        json = {
            "status": text,
            "visibility": visibility,
            "sensitive": sensitive,
        }

        if len(media_ids) > 0:
            json["media_ids"] = media_ids

        if spoiler_text is not None:
            json["spoiler_text"] = spoiler_text

        # pprint.pprint(data)

        response = self._request(
            url=url,
            method=method,
            headers=headers,
            json=json,
        )
        if not isinstance(response, dict):
            raise Exception(
                f"Unexpected response from Mastodon post API; expected JSON, got: {str(response)[:200]}"
            )
        if "id" not in response:
            raise Exception(
                f"Mastodon post API response missing 'id': {json} -> {str(response)[:200]}"
            )
        return response

    def upload_media(self, media_url):
        # print('【start】MastodonClient::upload_media()')

        method = "POST"
        endpoint = "/api/v2/media"
        url = f"{self.base_uri}{endpoint}"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        # URLからメディアのバイナリデータを取得
        response = requests.get(media_url)
        binary_data = response.content

        # ファイル名を生成（URLの最後の部分を使用）
        file_name = media_url.split("/")[-1]

        # Content-Typeをレスポンスヘッダーから取得、フォールバックで拡張子から推定
        content_type = response.headers.get('Content-Type',
                                            'application/octet-stream')

        # SVGはMastodonで受け付けられない場合があるのでPNGに変換を提案
        if 'svg' in content_type.lower():
            print(f"Warning: SVG detected ({content_type}). "
                  f"Some Mastodon instances may not support SVG uploads.")
            # SVGの場合はそのまま試すが、警告を出す
            content_type = 'image/svg+xml'

        # 拡張子ベースのフォールバック
        if content_type == 'application/octet-stream' or not content_type:
            if file_name.lower().endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif file_name.lower().endswith('.png'):
                content_type = 'image/png'
            elif file_name.lower().endswith('.gif'):
                content_type = 'image/gif'
            elif file_name.lower().endswith('.webp'):
                content_type = 'image/webp'
            elif file_name.lower().endswith('.svg'):
                content_type = 'image/svg+xml'
            else:
                content_type = 'image/jpeg'  # デフォルト

        # filesパラメータを正しく設定
        files = {"file": (file_name, binary_data, content_type)}

        # _requestメソッドの完全なリトライ機能を活用（503エラーにも対応）
        # retries=5: 2秒→4秒→8秒→16秒と待機（合計約30秒）
        response = self._request(
            url=url,
            method=method,
            headers=headers,
            files=files,
            retries=5,
            timeout=30,  # メディアアップロードは時間がかかる可能性があるのでタイムアウトを延長
        )
        if not isinstance(response, dict):
            raise Exception(
                f"Unexpected response from Mastodon media API; expected JSON, got: {str(response)[:200]}"
            )
        if "id" not in response:
            raise Exception(
                f"Mastodon media API response missing 'id' for file '{file_name}'"
            )

        # print('【end】MastodonClient::upload_media()')

        return response["id"]

    def get_account(self, account_id):
        # print('【start】MastodonClient::get_account()')

        endpoint = f"/api/v1/accounts/{account_id}"
        method = "GET"
        url = f"{self.base_uri}{endpoint}"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        response = self._request(url=url, method=method, headers=headers)

        # print('【end】MastodonClient::get_account()')

        return response

    def get_account_statuses(self, account_id):
        # print('【start】MastodonClient::get_account_statuses()')

        endpoint = f"/api/v1/accounts/{account_id}/statuses"
        url = f"{self.base_uri}{endpoint}"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        response = requests.get(url, headers=headers)

        # print('【end】MastodonClient::get_account_statuses()')

        return response.json()

    def get_account_followers(self, account_id):
        # print('【start】MastodonClient::get_account_followers()')

        endpoint = f"/api/v1/accounts/{account_id}/followers"
        method = "GET"
        url = f"{self.base_uri}{endpoint}"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        response = self._request(url=url, method=method, headers=headers)

        # print('【end】MastodonClient::get_account_followers()')

        return response

    def get_account_credentials(self):
        # print('【start】MastodonClient::get_account_credentials()')

        endpoint = "/api/v1/accounts/verify_credentials"
        method = "GET"
        url = f"{self.base_uri}{endpoint}"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        response = self._request(url=url, method=method, headers=headers)

        # print('【end】MastodonClient::get_account_credentials()')

        return response

    def search(
        self,
        q,
        resolve=False,
        limit=20,
        type=None,
        min_id: str | None = None,
    ):
        """_summary_

        Args:
            q (_type_): _description_
            resolve (bool, optional): WebFinger検索を行うかどうか. Defaults to False.
            limit: Integer. Maximum number of results to return, per type. Defaults to 20 results per category. Max 40 results per category.
            type (_type_, optional): String. Specify whether to search for only accounts, hashtags, statuses. Defaults to None.
            min_id: String. Returns results immediately newer than this ID. In effect, sets a cursor at this ID and paginates forward.

        Returns:
            _type_: _description_

        refs: https://docs.joinmastodon.org/methods/search/
        """
        # print('【start】MastodonClient::search()')

        endpoint = "/api/v2/search"
        method = "GET"
        url = f"{self.base_uri}{endpoint}"

        request_params = {
            "q": q,
            "resolve": resolve,
            "limit": limit,
        }

        if type is not None:
            request_params["type"] = type
        if min_id is not None:
            request_params["min_id"] = min_id

        response = self._request(url=url, method=method, params=request_params)

        # print('【end】MastodonClient::search()')

        return response
