import aiogram.fsm.context

class UrlStateHandler:

    def __init__(
        self,
        new_url: str | None,
        state: aiogram.fsm.context.FSMContext,
        prev_url_required: bool
    ):
        self.__new_url = new_url
        self.__state = state
        self.__prev_url_required = prev_url_required
        self.__state_data = None

    async def __aenter__(self) -> str:
        self.__state_data = await self.__state.get_data()

        if self.__state_data.get("url") is None:

            if self.__prev_url_required:
                raise ValueError("URL not found")

            self.__state_data["url"] = ""

        if self.__new_url is not None:
            self.__state_data["url"] += self.__new_url

        return self.__state_data["url"]

    async def __aexit__(self, *_):
        await self.__state.update_data(self.__state_data)
