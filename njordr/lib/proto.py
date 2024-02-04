"""
Njordr interaction protocol for Bots Services
"""

import typing
import pydantic

class Action(pydantic.BaseModel):
    method: typing.Literal["get", "post"]
    endpoint: str
    data: typing.Optional[str]


class PropModel(pydantic.BaseModel):
    """
    Prop
    Each prop contains text and an endpoint that will be called in case
    the user chooses it
    """

    text: str
    action: Action


class MessageModel(pydantic.BaseModel):
    """
    Message
    Each message contains text header and list of props that will be
    treated as buttons    
    """

    text: str
    props: typing.List[PropModel]

class Proto(pydantic.BaseModel):
    """
    Njordr protocol
    Bots APIs should form their responses according to this protocol
    """

    msg: MessageModel
