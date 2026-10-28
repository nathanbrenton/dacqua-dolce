"""PT54-A: validated customer configuration *requests*, not orderable products.

These inputs are never a price authority. All selections require commercial
review and are attached to a product inquiry rather than a cart line item.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SKU_FAMILY: dict[str, str] = {
    "DD15SOFT": "Refine", "DD20SOFT": "Refine",
    "DD15CATRV": "Essence", "DD20CATRV": "Essence",
    "DD15CLEARPTV": "Harmony", "DD15CLEARPL1": "Harmony",
    "DD15CLEARPL2": "Harmony", "DD15CLEARPL3": "Harmony",
    "DD5RO": "Origin", "DD6ROAE": "Origin",
}
FITTING_CHOICES: dict[str, tuple[str, str]] = {
    "V3007-03LF": ('3/4"', "Brass Sweat (Solder) Assembly LF"),
    "V3007-12LF": ('3/4"', "SharkBite Assembly"),
    "V3007-18": ('3/4"', "Plastic Male NPT"),
    "V3007-02LF": ('1"', "Brass Sweat (Solder) Assembly LF"),
    "V3007-13LF": ('1"', "SharkBite Assembly"),
    "V3007-04": ('1"', "Plastic Male NPT"),
    "V3007": ('1"', "Plastic Male NPT Elbow Assembly"),
    "V3007-22LF": ('1"', "Brass Press/Sweat Assembly LF"),
    "V3007-09LF": ('1.25" / 1.5"', "Brass Sweat (Solder) Assembly LF"),
    "V3007-05": ('1.25"', "Plastic Male NPT Assembly (1.25-inch only)"),
}
CARTRIDGE_CHOICES: dict[str, frozenset[str]] = {
    "sediment": frozenset({
        "Pleated — 30 micron", "Pleated polyester — 30 micron",
        "Pleated cellulose polyester — 1 micron",
        "Pleated cellulose polyester — 5 micron",
        "Pleated cellulose polyester — 20 micron",
        "Pleated cellulose polyester — 50 micron",
        "Pleated — 20 micron", "Sediment — 1 micron",
        "Sediment — 5 micron", "Sediment — 25 micron",
    }),
    "carbon": frozenset({
        'GAC — 4" diameter', 'PAC — 4" diameter (modified episolon carbon block)',
        "Non-Cellulose",
    }),
    "iron": frozenset({"Iron cartridge"}),
}
HARMONY_HOUSINGS = {
    "DD15CLEARPTV": 0,
    "DD15CLEARPL1": 1,
    "DD15CLEARPL2": 2,
    "DD15CLEARPL3": 3,
}


class RequestedFitting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_no: str = Field(max_length=32)
    size: str = Field(max_length=32)

    @model_validator(mode="after")
    def verify_known_fitting(self) -> "RequestedFitting":
        details = FITTING_CHOICES.get(self.order_no)
        if details is None or self.size != details[0]:
            raise ValueError("Fitting order number and actual hardware size must agree.")
        return self


class RequestedCartridge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: Literal[1, 2, 3]
    category: Literal["sediment", "carbon", "iron", "other"]
    cartridge: str | None = Field(default=None, max_length=120)
    other_description: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def verify_choice(self) -> "RequestedCartridge":
        if self.category == "other":
            if self.cartridge is not None:
                raise ValueError("Other cartridge requests cannot contain a catalog option.")
        elif self.other_description is not None:
            raise ValueError("Named cartridge choices cannot contain an other description.")
        elif self.cartridge is not None and self.cartridge not in CARTRIDGE_CHOICES[self.category]:
            raise ValueError("Unknown cartridge description for the selected category.")
        if self.other_description is not None and any(
            ord(character) < 32 for character in self.other_description
        ):
            raise ValueError("Invalid control characters in cartridge description.")
        return self


class ProductConfigurationRequest(BaseModel):
    """Unpriced customer-selected configuration; the product_id is verified separately."""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(max_length=32)
    tank_size_cf: Literal["1.5", "2.0"] | None = None
    finish: Literal["stainless", "neoprene"] | None = None
    valve: Literal["clack", "performance"] | None = None
    fitting: RequestedFitting | None = None
    housings: list[RequestedCartridge] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def verify_product_configuration(self) -> "ProductConfigurationRequest":
        family = SKU_FAMILY.get(self.sku)
        if family is None:
            raise ValueError("Unknown product SKU for configuration inquiry.")
        if family == "Origin":
            if any((self.tank_size_cf, self.finish, self.valve, self.fitting, self.housings)):
                raise ValueError("Origin does not support these whole-house configuration options.")
            return self
        if self.finish is None:
            raise ValueError("Tank finish is required for configured whole-house systems.")
        if family in {"Refine", "Essence"}:
            expected_size = "2.0" if self.sku.startswith("DD20") else "1.5"
            if self.tank_size_cf != expected_size:
                raise ValueError("Tank size must match the selected catalog product.")
            if self.valve is None:
                raise ValueError("A control valve selection is required.")
            if self.housings:
                raise ValueError("Pureline housing selections apply only to Harmony.")
            return self
        # 2.0 cf Harmony is a quotation inquiry only, not an existing saleable SKU.
        if self.tank_size_cf not in {"1.5", "2.0"}:
            raise ValueError("Harmony tank size is required.")
        if self.valve is not None or self.fitting is not None:
            raise ValueError("Harmony uses its pass-through valve and no Clack fitting selector.")
        count = HARMONY_HOUSINGS[self.sku]
        positions = [choice.position for choice in self.housings]
        if len(set(positions)) != len(positions) or any(position > count for position in positions):
            raise ValueError("Cartridge choices must occupy unique physical Pureline positions.")
        return self
