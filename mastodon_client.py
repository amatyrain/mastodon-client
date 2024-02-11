import json
import requests


class MastodonClient:
    def __init__(self, base_uri, access_token):
        self.base_uri = base_uri
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

    """_summary_

    """
    def _request(self, method, endpoint, data={}, headers=None):
        # print('【start】MasterdonApiHandler::_request()')

        url = f"{self.base_uri}{endpoint}"

        if len(headers) == 0:
            headers = self.headers

        print(f'url: {url}')
        print(f'method: {method}')
        print(f'data: {data}')

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                data=json.dumps(data),
            )
        except Exception as e:
            print(f"【MasterdonApiHandler】{e}")
            raise Exception(f"【MasterdonApiHandler】{e}")

        # print('【end】MasterdonApiHandler::_request()')

        return response

    def post(
        self,
        visibility: str,
        text: str,
        media_ids: list = [],
        sensitive: bool = False,
        spoiler_text: str | None = None,
    ) -> dict:
        """_summary_

        Args:
            visibility (str): public, unlisted, private, direct
            text (str): _description_
            media_ids (list): _description_
        """
        # print('【start】MasterdonApiHandler::post_status()')

        errors = []
        endpoint = "/api/v1/statuses"
        url = f"{self.base_uri}{endpoint}"
        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
            "Content-Type": "application/json",
        }
        data = {
            "status": text,
            "visibility": visibility,
            "sensitive": sensitive,
        }

        if len(media_ids) > 0:
            data["media_ids"] = media_ids

        if spoiler_text is not None:
            data["spoiler_text"] = spoiler_text

        # pprint.pprint(data)

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
        )

        # print(response.status_code)
        # pprint.pprint(json.loads(response.text))

        if response.status_code >= 400:
            print("【PosterMastodon】投稿に失敗しました。")
            raise Exception(f"mastodon_api: {response.text}\n{text}")

        # print('【end】MasterdonApiHandler::post_status()')

        return response.json()

    def upload_media(self, media_url):
        # print('【start】MasterdonApiHandler::upload_media()')

        endpoint = "/api/v2/media"
        url = f"{self.base_uri}{endpoint}"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        # url to media binary data
        response = requests.get(media_url)
        binary_data = response.content

        files = {
            "file": binary_data,
        }

        response = requests.post(url, headers=headers, files=files)
        media_id = response.json()["id"]

        # print('【end】MasterdonApiHandler::upload_media()')

        return media_id

    def get_account(self, account_id):
        # print('【start】MasterdonApiHandler::get_account()')

        endpoint = f"/api/v1/accounts/{account_id}"
        method = "GET"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        response = self._request(
            method=method,
            endpoint=endpoint,
            headers=headers
        )

        # print('【end】MasterdonApiHandler::get_account()')

        return response.json()

    def get_account_statuses(self, account_id):
        # print('【start】MasterdonApiHandler::get_account_statuses()')

        endpoint = f"/api/v1/accounts/{account_id}/statuses"
        url = f"{self.base_uri}{endpoint}"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        response = requests.get(url, headers=headers)

        # print('【end】MasterdonApiHandler::get_account_statuses()')

        return response.json()

    def get_account_followers(self, account_id):
        # print('【start】MasterdonApiHandler::get_account_followers()')

        endpoint = f"/api/v1/accounts/{account_id}/followers"
        method = "GET"
        url = f"{self.base_uri}{endpoint}"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        response = self._request(
            method=method,
            endpoint=endpoint,
            headers=headers
        )

        # print('【end】MasterdonApiHandler::get_account_followers()')

        return response.json()

    def get_account_credentials(self):
        # print('【start】MasterdonApiHandler::get_account_credentials()')

        endpoint = "/api/v1/accounts/verify_credentials"
        method = "GET"

        access_token = self.access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "curl/7.78.0",  # curlのUAを指定
        }

        response = self._request(
            method=method,
            endpoint=endpoint,
            headers=headers
        )

        # print('【end】MasterdonApiHandler::get_account_credentials()')

        return response.json()
