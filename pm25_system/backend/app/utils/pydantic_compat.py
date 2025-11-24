try:
    # Pydantic v2
    from pydantic import BaseModel as _BaseModel
    from pydantic import __version__ as _pyd_version
    _PYDANTIC_V2 = _pyd_version and _pyd_version.split('.')[0] == '2'
except Exception:
    from pydantic import BaseModel as _BaseModel
    _PYDANTIC_V2 = False


if _PYDANTIC_V2:
    class OrmBase(_BaseModel):
        model_config = {"from_attributes": True}
else:
    class OrmBase(_BaseModel):
        class Config:
            orm_mode = True
