from pydantic import BaseModel, ConfigDict


class SalesAreaRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enforcement_enabled: bool
    country_code: str
    region_codes: list[str]
    label: str
