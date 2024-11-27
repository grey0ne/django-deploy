from typing import Any, NamedTuple
import urllib.parse
import urllib.error
import urllib.request
import json


class Response(NamedTuple):
    body: str
    headers: dict[str, str]
    status: int
    error_count: int = 0

    def json(self) -> Any:
        try:
            output = json.loads(self.body)
        except json.JSONDecodeError:
            output = ""
        return output


def request(
    url: str,
    data: dict[str, Any] = {},
    params: dict[str, Any] = {},
    headers: dict[str, str] = {},
    method: str = "GET",
    data_as_json: bool = True,
    error_count: int = 0,
) -> Response:
    # HTTP Request based on urllib to get rid of external dependencies
    if not url.casefold().startswith("http"):
        raise urllib.error.URLError("Incorrect and possibly insecure protocol in url")
    method = method.upper()
    request_data = None
    headers = headers or {}
    data = data or {}
    params = params or {}
    headers = {"Accept": "application/json", **headers}

    if method == "GET":
        params = {**params, **data}
        data = {}

    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True, safe="/")

    if data:
        if data_as_json:
            request_data = json.dumps(data).encode()
            headers["Content-Type"] = "application/json; charset=UTF-8"
        else:
            request_data = urllib.parse.urlencode(data).encode()

    httprequest = urllib.request.Request(
        url, data=request_data, headers=headers, method=method
    )

    try:
        with urllib.request.urlopen(httprequest) as httpresponse:
            response = Response(
                headers=httpresponse.headers,
                status=httpresponse.status,
                body=httpresponse.read().decode(
                    httpresponse.headers.get_content_charset("utf-8")
                ),
            )
    except urllib.error.HTTPError as e:
        response = Response(
            body=str(e.reason),
            headers=dict(e.headers),
            status=e.code,
            error_count=error_count + 1,
        )

    return response
