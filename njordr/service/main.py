import sys
import logging

import json
import config

import httpx

import url_state_handler

import asyncio

import aiogram
import aiogram.types
import aiogram.filters
import aiogram.fsm.context

async def make_service_call(
    bot_config: config.BotConfig,
    endpoint: str
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{bot_config.url}{endpoint}')

            print(f"{type(response.content)}: {response.content}")
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        print(f"Caught: {e}")


async def start_handler(
    message: aiogram.types.Message,
    state: aiogram.fsm.context.FSMContext
):
    async with url_state_handler.UrlStateHandler("/", state, False) as url:
        bot_config = config.BotConfig(message.bot.id)
        await make_service_call(bot_config, url)


async def message_handler(
    message: aiogram.types.Message,
    state: aiogram.fsm.context.FSMContext
):
    async with url_state_handler.UrlStateHandler(None, state, True) as url:
        bot_config = config.BotConfig(message.bot.id)
        await message.answer(str(bot_config.url))


async def callback_query_handler(
    callback_query: aiogram.types.CallbackQuery,
    state: aiogram.fsm.context.FSMContext
):
    async with url_state_handler.UrlStateHandler(None, state, True) as url:
        bot_config = config.BotConfig(callback_query.bot.id)
        await callback_query.answer(str(bot_config.url))


async def main():
    njordr_config = config.NjordrConfig()
    dp = aiogram.Dispatcher()

    dp.message.register(start_handler, aiogram.filters.CommandStart())
    dp.message.register(message_handler)

    dp.callback_query.register(callback_query_handler)

    bots = []
    for bot_config in njordr_config.bots.values():
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

    await dp.start_polling(*bots)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
