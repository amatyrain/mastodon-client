import json
import requests


class MastodonClient:
    def __init__(self, base_uri, access_token):
        self.base_uri = base_uri
        self.access_token = access_token

    """_summary_

    """

    def post(
        self,
        visibility: str,
        text: str,
        media_ids: list = [],
    ) -> list:
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
        }

        if len(media_ids) > 0:
            data["media_ids"] = media_ids

        # pprint.pprint(data)

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
        )

        # print(response.status_code)
        # pprint.pprint(json.loads(response.text))

        if response.status_code == 200:
            print("【PosterMastodon】投稿が成功しました。")
        else:
            print("【PosterMastodon】投稿に失敗しました。")
            errors.append(f"mastodon_api: {response.text}\n{text}")

        # print('【end】MasterdonApiHandler::post_status()')

        return errors

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
