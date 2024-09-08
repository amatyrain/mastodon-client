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

    def _request(
        self, url: str, method: str, headers: dict,
        params=None, data=None, files=None,
    ):
        if headers is None:
            headers = self.headers

        print(f'url: {url}')
        print(f'method: {method}')
        print(f'data: {data}')
        print(f'params: {params}')

        response = requests.request(
            url=url,
            method=method,
            headers=headers,
            data=json.dumps(data),
            params=params,
            files=files,
        )
        return_response = response.json() if hasattr(response, "json") else response.text

        if response.status_code >= 400:
            print(f"Error: {return_response}")
            raise Exception(f'Error: {return_response}')

        return return_response

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
        # print('【start】MastodonClient::post_status()')

        method = "POST"
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

        return self._request(
            url=url,
            method=method,
            headers=headers,
            data=json.dumps(data),
        )

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

        # url to media binary data
        response = requests.get(media_url)
        binary_data = response.content

        files = {
            "file": binary_data,
        }

        response = self._request(
            url=url,
            method=method,
            headers=headers,
            files=files,
        )
        media_id = response["id"]

        # print('【end】MastodonClient::upload_media()')

        return media_id

    def get_account(self, account_id):
        # print('【start】MastodonClient::get_account()')

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

        # print('【end】MastodonClient::get_account()')

        return response.json()

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

        response = self._request(
            method=method,
            endpoint=endpoint,
            headers=headers
        )

        # print('【end】MastodonClient::get_account_followers()')

        return response.json()

    def get_account_credentials(self):
        # print('【start】MastodonClient::get_account_credentials()')

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

        # print('【end】MastodonClient::get_account_credentials()')

        return response.json()

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

        request_params = {
            "q": q,
            "resolve": resolve,
            "limit": limit,
        }

        if type is not None:
            request_params["type"] = type
        if min_id is not None:
            request_params["min_id"] = min_id

        response = self._request(
            method=method,
            endpoint=endpoint,
            params=request_params
        )

        # print('【end】MastodonClient::search()')

        return response.json()
