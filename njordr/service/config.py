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
    nickname: str
    token: str
    url: pydantic.HttpUrl

    @pydantic.field_validator('url')
    @classmethod
    def parse_url(cls, value: pydantic.HttpUrl, _: pydantic.ValidationInfo) -> str:
        return str(value).rstrip("/")

    @pydantic.field_validator('token')
    @classmethod
    def parse_telegram_token(cls, value: str, _: pydantic.ValidationInfo) -> str:
        if not re.match(r"^\d{10}:[a-zA-Z0-9]{35}$", value):
            raise ValueError("Token should match pattern bot_id:secret")

        return value


class TopSectionsConfigModel(
    roothazardlib.configs.ConstModel,
    pydantic.BaseModel
):
    server: roothazardlib.configs.ServerConfigModel
    tls: roothazardlib.configs.TLSConfigModel
    bots: typing.Dict[str, BotConfigModel]


class NjordrConfigModel(
    roothazardlib.configs.ConstModel,
    roothazardlib.configs.ConfigModel
):
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


class NjordrConfig(roothazardlib.configs.YamlConfig):
    _model: typing.Optional[NjordrConfigModel]

    def set_config(self, config):
        self._model = NjordrConfigModel(cfg=config)


def get_bot_config(bot_id: int) -> BotConfigModel:
    """
    Retrieve the configuration for an individual bot.

    Args:
        bot_id (str): The identifier of the bot.

    Returns:
        BotConfigModel: An instance of the BotConfigModel representing the
        configuration for the specified bot.
    """

    njordr_config: NjordrConfig = NjordrConfig()
    return njordr_config.cfg.bots[str(bot_id)]


def get_tls_config() -> roothazardlib.configs.TLSConfigModel:
    njordr_config: NjordrConfig = NjordrConfig()
    return njordr_config.cfg.tls
