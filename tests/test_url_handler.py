import pytest
from njordr_service.url_state_handler import UrlStateHandler

pytest_plugins = (
    'pytest_asyncio',
)


class StateMock:
    def __init__(self, data):
        self.data = data

    async def get_data(self):
        return self.data

    async def update_data(self, data):
        self.data = data


@pytest.mark.asyncio
@pytest.mark.parametrize("new_url,result", [
    ("", "/"),
    ("/", "/"),
    (".", "/")
    ("/////", "/"),
    ("../../", "/"),
    ("/hello", "/hello"),
    ("/hello.com/", "/hello.com"),
    ("/hello.com/abc", "/hello.com/abc"),
])
async def test_url_state_handler_root(new_url, result):
    state = StateMock({})

    async with UrlStateHandler(
        new_url=new_url, state=state, prev_url_required=False
    ) as url:
        assert url == result

    assert state.data.get("url") is not None
    assert state.data["url"] == result
