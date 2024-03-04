"""
Handles user url changes
"""

import typing
import pathlib
import logging
import aiogram.fsm.context

logger = logging.getLogger("njordr_service")

class UrlStateHandler:
    """
    A context manager for handling URL states within
    an Aiogram FSM (Finite State Machine) context.

    Args:
        new_url (str | None): The new URL segment to be appended.
        state (aiogram.fsm.context.FSMContext): The FSM context.
        prev_url_required (bool): Indicates whether a previous URL is required.

    Example Usage:
        async with UrlStateHandler("segment", fsm_state, True) as url:
            print(url)  # Use the url within this context

    Returns:
        str: The resulting URL after applying the new_url and handling previous URL conditions.
    """

    def __init__(
        self,
        new_url: str | None,
        state: aiogram.fsm.context.FSMContext,
        prev_url_required: bool
    ):
        self.__new_url = new_url
        self.__state = state
        self.__prev_url_required = prev_url_required
        self.__state_data: typing.Optional[dict[str, typing.Any]] = None

    async def __aenter__(self) -> str:
        self.__state_data = await self.__state.get_data()

        if self.__prev_url_required and self.__state_data.get("url") is None:
            raise ValueError("URL not found")

        if not self.__prev_url_required or self.__state_data.get("url") is None:
            self.__state_data["url"] = ""

        if self.__new_url is not None:
            path = pathlib.Path(self.__state_data["url"])
            path /= self.__new_url
            path = path.resolve()

            self.__state_data["url"] = path.as_posix()

        logger.info("Formed base url: %s", self.__state_data["url"])

        return self.__state_data["url"]

    async def __aexit__(self, *_):
        await self.__state.update_data(self.__state_data)
