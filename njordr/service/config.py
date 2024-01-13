"""
Configuration file entities models
"""

import re
import typing
from typing import Any
import pydantic

import yaml

class BotConfigModel(pydantic.BaseModel):
    """
    A Pydantic model representing the configuration for a Telegram bot.

    Attributes:
        nickname (str): The nickname of the bot.
        token (str): The token associated with the Telegram bot.
        url (pydantic.HttpUrl): The URL associated with the bot backedn API.

    Class Methods:
        parse_telegram_token(cls, value: str, _: pydantic.ValidationInfo) -> str:
            A class method to validate and parse the Telegram bot token.
            Raises a ValueError if the token does not match the expected pattern.

    Methods:
        __setattr__(self, _: str, __: typing.Any) -> None:
            Overrides the default __setattr__ method to make the object readonly.
            Raises an AttributeError if any attempt is made to modify the object.

    Note:
        This class is a Pydantic BaseModel, providing data validation and parsing.
        The `parse_telegram_token` method validates the format of the Telegram bot token.
        The object is made readonly, preventing modifications after instantiation.
    """

    nickname: str
    token: str
    url: pydantic.HttpUrl

    @pydantic.field_validator('token')
    @classmethod
    def parse_telegram_token(cls, value: str, _: pydantic.ValidationInfo) -> str:
        """
        Validate and parse the Telegram bot token.

        Args:
            value (str): The Telegram bot token to be validated.
            _: Ignored parameter, required for Pydantic validators.

        Returns:
            str: The validated Telegram bot token.

        Raises:
            ValueError: If the token does not match the expected pattern.
        """

        if not re.match(r"^\d{10}:[a-zA-Z0-9]{35}$", value):
            raise ValueError("Token should match pattern bot_id:secret")

        return value

    def __setattr__(self, _: str, __: typing.Any) -> None:
        """
        Override the default __setattr__ method to make the object readonly.

        Args:
            _: Ignored parameter.
            __: Ignored parameter.

        Raises:
            AttributeError: If any attempt is made to modify the object.
        """

        raise AttributeError("Object is readonly")


class TLSConfigModel(pydantic.BaseModel):
    cert: pydantic.FilePath
    key: pydantic.FilePath
    ca: pydantic.FilePath

    def __setattr__(self, _: str, __: typing.Any) -> None:
        """
        Override the default __setattr__ method to make the object readonly.

        Args:
            _: Ignored parameter.
            __: Ignored parameter.

        Raises:
            AttributeError: If any attempt is made to modify the object.
        """

        raise AttributeError("Object is readonly")


class TopSectionsConfigModel(pydantic.BaseModel):
    port: pydantic.PositiveInt
    tls: TLSConfigModel
    bots: typing.Dict[str, BotConfigModel]

    def __setattr__(self, _: str, __: typing.Any) -> None:
        """
        Override the default __setattr__ method to make the object readonly.

        Args:
            _: Ignored parameter.
            __: Ignored parameter.

        Raises:
            AttributeError: If any attempt is made to modify the object.
        """

        raise AttributeError("Object is readonly")


class NjordrConfigModel(pydantic.BaseModel):
    """
    A Pydantic model representing the configuration for the Njordr application.

    Attributes:
        bots (typing.Dict[str, BotConfigModel]):
            A dictionary mapping bot ids to their respective configurations.

    Methods:
        __setattr__(self, _: str, __: typing.Any) -> None:
            Overrides the default __setattr__ method to make the object readonly.
            Raises an AttributeError if any attempt is made to modify the object.

        __getitem__(self, key: str) -> BotConfigModel:
            Retrieves the configuration for a specific bot.

        Parameters:
            key (str): The name of the bot.

        Returns:
            BotConfigModel: The configuration for the specified bot.

    Note:
        This class is a Pydantic BaseModel, providing data validation and parsing.
        The object is made readonly, preventing modifications after instantiation.
    """

    cfg: TopSectionsConfigModel

    def __setattr__(self, _: str, __: typing.Any) -> None:
        """
        Override the default __setattr__ method to make the object readonly.

        Args:
            _: Ignored parameter.
            __: Ignored parameter.

        Raises:
            AttributeError: If any attempt is made to modify the object.
        """

        raise AttributeError("Object is readonly")

    def __getitem__(self, key: str) -> BotConfigModel:
        """
        Retrieve the configuration for a specific bot.

        Args:
            key (str): The name of the bot.

        Returns:
            BotConfigModel: The configuration for the specified bot.
        """

        return self.cfg.bots[key]


class Singletone(type):
    """
    Singletone metaclass for making singletones
    """

    __instances: dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)

        return cls.__instances[cls]

class NjordrConfig(metaclass=Singletone):
    """
    NjordrConfig singletone
    """

    __model: typing.Optional[NjordrConfigModel] = None

    def __init__(self) -> None:
        if self.__model is None:
            with open("config.yaml", mode="r", encoding="utf-8") as config_file:
                config_obj = yaml.safe_load(config_file)

            self.__model = NjordrConfigModel(cfg=config_obj)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        if "__" in name:
            super().__setattr__(name, value)
        else:
            raise AttributeError("Object is readonly")

    def __getattribute__(self, name: str) -> Any:
        if "__" in name:
            return super().__getattribute__(name)

        return getattr(self.__model, name)


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
