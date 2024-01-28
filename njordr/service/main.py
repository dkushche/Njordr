"""
Njordr broker service main
* Listens for telegram requests
* Proxies to specific bots
* Replies back in the telegram
"""

import os
import sys
import logging
import asyncio

import httpx
import uvicorn
import fastapi

import aiogram
import aiogram.types
import aiogram.filters
import aiogram.fsm.context

import url_state_handler
import config

async def make_service_call(
    bot_config: config.BotConfigModel,
    user: aiogram.types.User,
    endpoint: str
):
    """
    Make an asynchronous HTTP service call.

    This function sends an HTTP GET request to the specified endpoint
    using the provided bot configuration.

    Args:
        bot_config (config.BotConfigModel): The bot configuration.
        endpoint (str): The endpoint to call.

    Example Usage:
        await make_service_call(bot_config_instance, "/some_endpoint")
    """

    tls_config = config.get_tls_config()

    try:
        client = httpx.Client(
            verify=tls_config.ca,
            cert=(
                tls_config.client_cert,
                tls_config.client_key
            )
        )

        headers = {
            'njordr_client': f"tg:{user.id}"
        }

        response = client.get(
            f'{bot_config.url}{endpoint}',
            headers=headers
        )

        print(f"{type(response.content)}: {response.content!r}")
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        print(f"Caught: {e}")


async def start_handler(
    message: aiogram.types.Message,
    state: aiogram.fsm.context.FSMContext
):
    """
    Handle the '/start' command.

    This function is intended to be used as a
    command handler for the '/start' command in Aiogram.
    It initializes a URL state using the UrlStateHandler,retrieves the bot
    configuration based on the message's bot ID, and makes a service call
    using the configured bot and URL.

    Args:
        message (aiogram.types.Message): The incoming message instance.
        state (aiogram.fsm.context.FSMContext): The FSM context.

    Example Usage:
        dp.message.register(start_handler, commands=['start'])
    """

    async with url_state_handler.UrlStateHandler("/", state, False) as url:
        if message.bot is None or message.from_user is None:
            raise ValueError("Unexpected behaviour")

        bot_config: config.BotConfigModel = config.get_bot_config(message.bot.id)
        await make_service_call(bot_config, message.from_user, url)


async def message_handler(
    message: aiogram.types.Message,
    state: aiogram.fsm.context.FSMContext
):
    """
    Handle incoming messages.

    This function is intended to be used as a message handler in Aiogram.
    It retrieves the bot configuration based on the message's bot ID,
    and replies to the message with the configured URL.

    Args:
        message (aiogram.types.Message): The incoming message instance.
        state (aiogram.fsm.context.FSMContext): The FSM context.

    Example Usage:
        dp.message.register(message_handler)
    """

    async with url_state_handler.UrlStateHandler(None, state, True) as url:
        if message.bot is None or message.from_user is None:
            raise ValueError("Unexpected behaviour")

        bot_config: config.BotConfigModel = config.get_bot_config(message.bot.id)
        await make_service_call(bot_config, message.from_user, url)


async def callback_query_handler(
    callback_query: aiogram.types.CallbackQuery,
    state: aiogram.fsm.context.FSMContext
):
    """
    Handle callback queries.

    This function is intended to be used as a callback query handler in Aiogram.
    It retrieves the bot configuration based on the callback_query's bot ID,
    and answers the callback query with the configured URL.

    Args:
        callback_query (aiogram.types.CallbackQuery): The callback query instance.
        state (aiogram.fsm.context.FSMContext): The FSM context.

    Example Usage:
        dp.callback_query.register(callback_query_handler)
    """

    async with url_state_handler.UrlStateHandler(None, state, True) as url:
        if callback_query.bot is None or callback_query.from_user is None:
            raise ValueError("Unexpected behaviour")

        bot_config: config.BotConfigModel = config.get_bot_config(callback_query.bot.id)
        await make_service_call(bot_config, callback_query.from_user, url)


notifications_api = fastapi.FastAPI()

@notifications_api.post("/notifiaction")
async def notification(req: fastapi.Request):
    """
    Under development
    """

    print(req)
    return {"message": "kek"}


async def main():
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
