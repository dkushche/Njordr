import pydantic

class Prop(pydantic.BaseModel):
    text: str
    action_url: str

class Proto(pydantic.BaseModel):
    text: str
