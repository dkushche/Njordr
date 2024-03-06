"""
Njordr broker service main
* Listens for telegram requests
* Proxies to specific bots
* Replies back in the telegram
"""

import os
import json
import typing
import asyncio
import logging.config

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

logger = logging.getLogger("njordr_service")

def generate_keyboard(
    props: list[njordr.PropModel]
) -> typing.Optional[aiogram.types.InlineKeyboardMarkup]:
    """
    Generates inline keyboard fomr service message props
    """

    if len(props) == 0:
        return None

    buttons = []

    logger.info("Generating inline keyboard")

    for prop in props:
        logger.info(
            "Generate button with text: %s; callback_data: %s",
            prop.text, prop.action.model_dump_json()
        )

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

    logger.info("Generation of inline ketboard finished")

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

    logger.info(
        "Making service call %s(%s)",
        action.method, request_parameters
    )

    try:
        response = await getattr(async_client, action.method)(**request_parameters)
    except httpx.ConnectError as error:
        logger.error(
            "Connection error: %s; %s", request_parameters['url'], error
        )

        return None

    service_response = json.loads(response.contect.decode("utf-8"))
    message = njordr.Proto(msg=service_response).msg

    logger.info("Service response: %s", message)

    return message


async def start_handler(
    message: aiogram.types.Message,
    state: aiogram.fsm.context.FSMContext
):
    """
    Handles /start in user chat
    """

    async with url_state_handler.UrlStateHandler("", state, False) as url:
        if message.bot is None or message.from_user is None:
            raise ValueError("Unexpected behaviour")

        bot_config: config.BotConfigModel = config.get_bot_config(message.bot.id)
        action: njordr.Action = njordr.Action(
            method="get", endpoint=url, data=None
        )

        logger.info(
            "Received message with action: %s", action
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
            logger.error("Service message is None")

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

    logger.info(
        "Received message with action: %s", action
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
            logger.error("Service message is None")

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

    if not isinstance(callback_query.message, aiogram.types.Message):
        logger.critical(
            "Problem with message in callback query: %s",
            callback_query.message
        )
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

    logger.info(
        "Received callback querry with action: %s", action
    )

    async with url_state_handler.UrlStateHandler(
        action.endpoint, state, True
    ) as url:
        if callback_query.bot is None or callback_query.from_user is None:
            raise ValueError("Unexpected behaviour")

        bot_config: config.BotConfigModel = config.get_bot_config(
            callback_query.bot.id
        )

        service_msg = await make_service_call(
            bot_config, callback_query.from_user, action, url
        )

        if service_msg is not None:
            keyboard = generate_keyboard(service_msg.props)

            await callback_query.message.edit_text(
                text=service_msg.text,
                reply_markup=keyboard
            )
        else:
            logger.error("Service message is None")

            await callback_query.message.answer(
                text="Internal error",
                reply_markup=None
            )


notifications_api = fastapi.FastAPI()

@notifications_api.post("/notifiaction")
async def notification(req: fastapi.Request):
    """
    Under development
    """

    logger.info("Notification: %s", req)
    return {"result": "Unsupported"}


async def njordr_service():
    """
    Main function for initializing and running the Aiogram bots.

    This function reads Njordr configuration, sets up Aiogram Dispatcher,
    registers message and callback handlers, initializes bot instances for each configured bot,
    sets the '/start' command for each bot, and starts polling for incoming updates.

    Example Usage:
        asyncio.run(njordr_service())
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

        logger.info(
            "Register handler for %s:%s",
            bot_config.nickname, bot_config.url
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
    """Run async njordr service"""

    with open(
        "njordr_service/logging_config.json",
        encoding="utf-8"
    ) as logging_cgf_fd:
        logging_cfg = json.load(logging_cgf_fd)

    logging.config.dictConfig(logging_cfg)

    coroutine = njordr_service()

    asyncio.run(coroutine)


if __name__ == "__main__":
    main()
