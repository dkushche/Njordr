import pydantic
import typing

class PropModel(pydantic.BaseModel):
    text: str
    action_url: str

class MessageModel(pydantic.BaseModel):
    text: str
    actions: typing.List[PropModel]

class Proto(pydantic.BaseModel):
    msg: MessageModel
