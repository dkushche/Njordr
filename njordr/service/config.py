import re
import yaml
import typing
import pydantic

class BotConfigModel(pydantic.BaseModel):
    nickname: str
    token: str
    url: pydantic.HttpUrl

    @pydantic.field_validator('token')
    @classmethod
    def parse_telegram_token(cls, value: str, _: pydantic.ValidationInfo):
        if not re.match(r"^\d{10}:[a-zA-Z0-9]{35}$", value):
            raise ValueError("Token should match pattern bot_id:secret")

        return value

    def __setattr__(self, _: str, __: typing.Any) -> None:
        raise AttributeError("Object is readonly")


class NjordrConfigModel(pydantic.BaseModel):
    bots: typing.Dict[str, BotConfigModel]

    def __setattr__(self, _: str, __: typing.Any) -> None:
        raise AttributeError("Object is readonly")

    def __getitem__(self, key: str):
        return self.bots[key]


class NjordrConfig:
    __instance = None

    def __new__(cls) -> type:
        if cls.__instance is None:

            with open("config.yaml", mode="r", encoding="utf-8") as config_file:
                config_obj = yaml.load(config_file)

            cls.__instance = NjordrConfigModel(bots=config_obj)

        return cls.__instance


class BotConfig:

    def __new__(cls, bot_id):
        njordr_config = NjordrConfig()
        return njordr_config[str(bot_id)]
