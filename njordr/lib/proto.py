"""
Njordr interaction protocol for Bots Services
"""

import typing
import pydantic

class PropModel(pydantic.BaseModel):
    """
    Prop
    Each prop contains text and an endpoint that will be called in case
    the user chooses it
    """

    text: str
    action_endpoint: str

class MessageModel(pydantic.BaseModel):
    """
    Message
    Each message contains text header and list of props that will be
    treated as buttons    
    """

    text: str
    actions: typing.List[PropModel]

class Proto(pydantic.BaseModel):
    """
    Njordr protocol
    Bots APIs should form their responses according to this protocol
    """

    msg: MessageModel
