"""
Configuration file entities models
"""

import re
import typing
import pydantic

import roothazardlib.configs

class BotConfigModel(
    roothazardlib.configs.ConstModel,
    pydantic.BaseModel
):
    """
    Njordr will connect to each tg bot listen in this section
    and then redirect to specific instance
    """

    nickname: str
    token: str
    url: pydantic.HttpUrl

    @pydantic.field_validator('url')
    @classmethod
    def parse_url(cls, value: pydantic.HttpUrl, _: pydantic.ValidationInfo) -> str:
        """
        '/' In the end creates problems for me
        """

        return str(value).rstrip("/")

    @pydantic.field_validator('token')
    @classmethod
    def parse_telegram_token(cls, value: str, _: pydantic.ValidationInfo) -> str:
        '''
        Token it's not just a string lets validate it additionaly
        '''

        if not re.match(r"^\d{10}:[a-zA-Z0-9]{35}$", value):
            raise ValueError("Token should match pattern bot_id:secret")

        return value


class TopSectionsConfigModel(
    roothazardlib.configs.ConstModel,
    pydantic.BaseModel
):
    """
    Njordr serves connect to other services and configured
    for different tg bots
    """

    server: roothazardlib.configs.ServerConfigModel
    tls: roothazardlib.configs.TLSConfigModel
    bots: typing.Dict[str, BotConfigModel]


class NjordrConfigModel(
    roothazardlib.configs.ConstModel,
    roothazardlib.configs.ConfigModel
):
    """
    Just high level model to parse object
    """

    cfg: TopSectionsConfigModel

    def __getitem__(self, key: str) -> BotConfigModel:
        """
        Retrieve the configuration for a specific bot.

        Args:
            key (str): The name of the bot.

        Returns:
            BotConfigModel: The configuration for the specified bot.
        """

        return self.cfg.bots[key]


class NjordrConfig(roothazardlib.configs.YamlConfig): # pylint: disable=too-few-public-methods
    """
    Njordr specific config
    """

    _model: typing.Optional[NjordrConfigModel]


def get_bot_config(bot_id: int) -> BotConfigModel:
    """
    Retrieve the configuration for an individual bot.

    Args:
        bot_id (str): The identifier of the bot.

    Returns:
        BotConfigModel: An instance of the BotConfigModel representing the
        configuration for the specified bot.
    """

    njordr_config: NjordrConfig = NjordrConfig(None)
    return njordr_config.cfg.bots[str(bot_id)]


def get_tls_config() -> roothazardlib.configs.TLSConfigModel:
    """
    Get tls part of config
    """

    njordr_config: NjordrConfig = NjordrConfig(None)
    return njordr_config.cfg.tls
