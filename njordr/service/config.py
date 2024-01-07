"""
Configuration file entities models
"""

import re
import typing
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

    def __getitem__(self, key: str) -> BotConfigModel:
        """
        Retrieve the configuration for a specific bot.

        Args:
            key (str): The name of the bot.

        Returns:
            BotConfigModel: The configuration for the specified bot.
        """

        return self.bots[key]

class NjordrConfig:
    """
    Singleton class representing the configuration for the Njordr application.

    This class uses the Singleton pattern to ensure that only one instance of
    the configuration is created, and subsequent attempts to create instances
    return the existing instance.

    Methods:
        __new__(cls) -> type:
            Creates a new instance of the NjordrConfigModel using data from the
            "config.yaml" file. Returns the existing instance if it already exists.

    Note:
        The configuration is loaded from a YAML file and used to create an instance
        of the NjordrConfigModel class. Subsequent attempts to create instances return
        the same configuration, ensuring that there is only one configuration object.
    """

    __instance: NjordrConfigModel | None = None

    def __new__(cls) -> NjordrConfigModel:
        """
        Create a new instance of the NjordrConfigModel.

        Returns:
            NjordrConfigModel:
                The instance of NjordrConfigModel created from the "config.yaml" file.
        """

        if cls.__instance is None:
            with open("config.yaml", mode="r", encoding="utf-8") as config_file:
                config_obj = yaml.safe_load(config_file)

            cls.__instance = NjordrConfigModel(bots=config_obj)

        return cls.__instance

class BotConfig:
    """
    Class providing access to the configuration of a specific bot from the Njordr application.

    This class is designed to be used to retrieve the configuration of a specific bot based
    on its ID from the NjordrConfigModel.

    Methods:
        __new__(cls, bot_id) -> NjordrConfigModel:
            Creates a new instance of the NjordrConfigModel using the NjordrConfig singleton
            and retrieves the configuration for the specified bot ID.

        Parameters:
            bot_id: The ID of the bot for which to retrieve the configuration.

        Returns:
            NjordrConfigModel: The configuration for the specified bot.
    """

    def __new__(cls, bot_id) -> BotConfigModel:
        """
        Create a new instance of the NjordrConfigModel and retrieve the configuration for a bot.

        Args:
            bot_id: The ID of the bot for which to retrieve the configuration.

        Returns:
            BotConfigModel: The configuration for the specified bot.
        """

        njordr_config: NjordrConfigModel = NjordrConfig()

        return njordr_config[str(bot_id)]
