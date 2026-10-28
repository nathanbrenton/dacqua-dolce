"""Render validated, non-priced configuration inquiries for staff review."""

from app.schemas.product_configuration import (
    FITTING_CHOICES,
    SKU_FAMILY,
    ProductConfigurationRequest,
)
from app.services.option_approval import review_fitting, review_pureline_cartridge


def configuration_inquiry_text(configuration: ProductConfigurationRequest) -> str:
    family = SKU_FAMILY[configuration.sku]
    lines = [
        "Customer-requested configuration (NOT a priced or approved order):",
        f"Catalog reference SKU: {configuration.sku} ({family})",
    ]
    if family == "Origin":
        lines.append("Origin configuration: standard catalog stage selection.")
        return "\n".join(lines)
    lines.extend([
        f"Requested tank size: {configuration.tank_size_cf} cubic feet",
        f"Tank finish: {configuration.finish}",
    ])
    if configuration.finish == "neoprene":
        lines.append(
            "Black neoprene jacket requested: displayed +$100 option; "
            "NOT included in any cart amount. Confirm final quote."
        )
    if family in {"Refine", "Essence"}:
        lines.append(f"Requested valve: {configuration.valve}")
        if configuration.fitting is None:
            lines.append("Required fitting: customer needs assistance selecting hardware.")
        else:
            description = FITTING_CHOICES[configuration.fitting.order_no][1]
            decision = review_fitting(configuration.valve, configuration.fitting.order_no)
            lines.append(
                f"Requested fitting: {configuration.fitting.size} — {description} "
                f"({configuration.fitting.order_no}); fitment and price unverified."
            )
            lines.append(
                f"Fitting approval for {configuration.valve} valve: "
                f"{decision.approval_status.upper()}; staff compatibility, correct part, "
                "and commercial price confirmation required before a formal offer."
            )
            if configuration.valve == "performance":
                lines.append(
                    "Confirm Clack-reference fitting compatibility with Performance valve."
                )
    else:
        if configuration.tank_size_cf == "2.0":
            lines.append(
                "Harmony 2.0 cf: no authorized saleable SKU or price; staff quotation required."
            )
        for choice in sorted(configuration.housings, key=lambda value: value.position):
            decision = review_pureline_cartridge(choice.category, choice.cartridge)
            option = choice.cartridge or choice.other_description or "specific option pending"
            lines.append(
                f"Pureline housing {choice.position}: {choice.category} — {option}; "
                "compatibility and price unverified."
            )
            lines.append(
                f"Pureline housing {choice.position} approval: "
                f"{decision.approval_status.upper()}; staff must confirm model, "
                "housing compatibility, availability, and price before a formal offer."
            )
    lines.append(
        "Confirm availability, compatibility, commercial terms, and pricing before ordering."
    )
    return "\n".join(lines)
