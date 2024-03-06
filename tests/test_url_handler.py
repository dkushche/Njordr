import pytest
from njordr_service.url_state_handler import UrlStateHandler

pytest_plugins = ('pytest_asyncio',)

class StateMock:
    def __init__(self, data):
        self.data = data

    async def get_data(self):
        return self.data

    async def update_data(self, data):
        self.data = data


@pytest.mark.asyncio
async def test_url_state_handler_root():
    state = StateMock({})

    async with UrlStateHandler(
        new_url="/", state=state, prev_url_required=False
    ) as url:
        assert url == "/"

    assert state.data.get("url") is not None
    assert state.data["url"] == "/"
