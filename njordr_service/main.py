"""
Njordr broker service main
* Listens for telegram requests
* Proxies to specific bots
* Replies back in the telegram
"""

import os
import sys
import json
import typing
import logging
import asyncio

import httpx
import uvicorn
import fastapi

import pydantic

import aiogram
import aiogram.types
import aiogram.filters
import aiogram.fsm.context

import url_state_handler
import config
import njordr

BOTS_SESSIONS: dict[pydantic.HttpUrl, httpx.Client] = {}

def generate_keyboard(
    props: list[njordr.PropModel]
) -> typing.Optional[aiogram.types.InlineKeyboardMarkup]:
    """
    Generates inline keyboard fomr service message props
    """

    if len(props) == 0:
        return None

    buttons = []

    for prop in props:
        buttons.append(
            [
                aiogram.types.InlineKeyboardButton(
                    text=prop.text,
                    callback_data=prop.action.model_dump_json()
                )
            ]
        )

    keyboard = aiogram.types.InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    return keyboard


async def make_service_call(
    bot_config: config.BotConfigModel,
    user: aiogram.types.User,
    action: njordr.Action,
    full_endpoint: str
) -> typing.Optional[njordr.MessageModel]:
    """
    Make async call to end service to get MessageModel
    """

    async_client = BOTS_SESSIONS[bot_config.url]

    headers = {
        'assume_role': f"tg:{user.id}"
    }

    request_parameters = {
        "headers": headers,
        "url": f"{bot_config.url}{full_endpoint}",
    }

    if action.data is not None:
        request_parameters["data"] = action.data

    try:
        response = await getattr(async_client, action.method)(**request_parameters)
    except httpx.ConnectError as error:
        logging.error(
            "Connection error: %s; %s", request_parameters['url'], error
        )

        return None

    service_response = json.loads(response.contect.decode("utf-8"))
    return njordr.Proto(msg=service_response).msg


async def start_handler(
    message: aiogram.types.Message,
    state: aiogram.fsm.context.FSMContext
):
    """
    Handles /start in user chat
    """

    async with url_state_handler.UrlStateHandler("/", state, False) as url:
        if message.bot is None or message.from_user is None:
            raise ValueError("Unexpected behaviour")

        bot_config: config.BotConfigModel = config.get_bot_config(message.bot.id)
        action: njordr.Action = njordr.Action(
            method="get", endpoint="/", data=None
        )

        service_msg = await make_service_call(
            bot_config, message.from_user, action, url
        )

        if service_msg is not None:
            keyboard = generate_keyboard(service_msg.props)

            await message.answer(
                text=service_msg.text,
                reply_markup=keyboard
            )
        else:
            await message.answer(
                text="Internal error",
                reply_markup=None
            )


async def message_handler(
    message: aiogram.types.Message,
    state: aiogram.fsm.context.FSMContext
):
    """
    handles manual typing in user chat
    """

    action: njordr.Action = njordr.Action(
        method="post", endpoint="", data=message.text
    )

    async with url_state_handler.UrlStateHandler(None, state, True) as url:
        if message.bot is None or message.from_user is None:
            raise ValueError("Unexpected behaviour")

        bot_config: config.BotConfigModel = config.get_bot_config(message.bot.id)

        service_msg = await make_service_call(
            bot_config, message.from_user, action, url
        )

        if service_msg is not None:
            keyboard = generate_keyboard(service_msg.props)

            await message.answer(
                text=service_msg.text,
                reply_markup=keyboard
            )
        else:
            await message.answer(
                text="Internal error",
                reply_markup=None
            )


async def callback_query_handler(
    callback_query: aiogram.types.CallbackQuery,
    state: aiogram.fsm.context.FSMContext
) -> None:
    """
    Handles buttons clicks in user chat
    """

    if callback_query.message is None:
        logging.critical("No message in callback query")
        return

    if callback_query.data is None:
        await callback_query.message.answer(
            text="Internal error",
            reply_markup=None
        )
        return

    cb_data = json.loads(callback_query.data)
    action: njordr.Action = njordr.Action(
        **cb_data
    )

    async with url_state_handler.UrlStateHandler(action.endpoint, state, True) as url:
        if callback_query.bot is None or callback_query.from_user is None:
            raise ValueError("Unexpected behaviour")

        bot_config: config.BotConfigModel = config.get_bot_config(callback_query.bot.id)

        service_msg = await make_service_call(
            bot_config, callback_query.from_user, action, url
        )

        if service_msg is None:
            await callback_query.message.answer(
                text="Internal error",
                reply_markup=None
            )
        else:
            keyboard = generate_keyboard(service_msg.props)

            await callback_query.message.edit_text(
                text=service_msg.text,
                reply_markup=keyboard
            )


notifications_api = fastapi.FastAPI()

@notifications_api.post("/notifiaction")
async def notification(req: fastapi.Request):
    """
    Under development
    """

    print(req)
    return {"result": "Unsupported"}


async def njordr_service():
    """
    Main function for initializing and running the Aiogram bots.

    This function reads Njordr configuration, sets up Aiogram Dispatcher,
    registers message and callback handlers, initializes bot instances for each configured bot,
    sets the '/start' command for each bot, and starts polling for incoming updates.

    Example Usage:
        asyncio.run(main())
    """

    njordr_config = config.NjordrConfig(
        f'{os.environ["SERVICE_CONFIG_DIR"]}/config.yaml'
    )

    dp = aiogram.Dispatcher()

    dp.message.register(start_handler, aiogram.filters.CommandStart())
    dp.message.register(message_handler)

    dp.callback_query.register(callback_query_handler)

    bots = []
    for bot_config in njordr_config.cfg.bots.values():
        bot = aiogram.Bot(
            token=bot_config.token,
            parse_mode=aiogram.enums.ParseMode.HTML,
        )

        BOTS_SESSIONS[bot_config.url] = httpx.AsyncClient(
            verify=njordr_config.cfg.tls.ca,
            cert=(
                njordr_config.cfg.tls.client_cert,
                njordr_config.cfg.tls.client_key
            )
        )

        await bot.set_my_commands(
            [
                { 'command': '/start', 'description': 'Start'}
            ]
        )

        bots.append(bot)

    notificaton_config = uvicorn.Config(
        "main:notifications_api",
        host=njordr_config.cfg.server.host,
        port=njordr_config.cfg.server.port
    )

    notification_server = uvicorn.Server(notificaton_config)

    asyncio.create_task(notification_server.serve())

    await asyncio.create_task(dp.start_polling(*bots))
    await notification_server.shutdown()

    for async_client in BOTS_SESSIONS.values():
        await async_client.aclose()


def main():
    coroutine = njordr_service()

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(coroutine)


if __name__ == "__main__":
    main()
