import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy import select

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
)
from app.models.customer import (
    CustomerAddress,
    CustomerProfile,
)
from app.schemas.account import (
    AddressCreate,
    AddressRead,
    CustomerProfileRead,
    CustomerProfileUpdate,
)
from app.services.audit import (
    record_audit_event,
)

router = APIRouter(
    prefix="/account",
    tags=["account"],
)


def address_read(
    address: CustomerAddress,
) -> AddressRead:
    return AddressRead(
        id=str(address.id),
        label=address.label,
        line1=address.line1,
        line2=address.line2,
        city=address.city,
        region_code=address.region_code,
        postal_code=address.postal_code,
        country_code=address.country_code,
        is_default_shipping=(address.is_default_shipping),
        is_default_billing=(address.is_default_billing),
    )


@router.get(
    "/profile",
    response_model=CustomerProfileRead,
)
def get_profile(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CustomerProfileRead:
    profile = db.get(
        CustomerProfile,
        current_user.id,
    )

    addresses = db.scalars(
        select(CustomerAddress)
        .where(CustomerAddress.user_id == current_user.id)
        .order_by(CustomerAddress.created_at)
    ).all()

    return CustomerProfileRead(
        email=current_user.email,
        first_name=(profile.first_name if profile is not None else None),
        last_name=(profile.last_name if profile is not None else None),
        phone=(profile.phone if profile is not None else None),
        addresses=[address_read(address) for address in addresses],
    )


@router.put(
    "/profile",
    response_model=CustomerProfileRead,
)
def update_profile(
    payload: CustomerProfileUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CustomerProfileRead:
    profile = db.get(
        CustomerProfile,
        current_user.id,
    )

    if profile is None:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)

    profile.first_name = payload.first_name
    profile.last_name = payload.last_name
    profile.phone = payload.phone

    record_audit_event(
        db,
        action="customer.profile_updated",
        entity_type="customer_profile",
        entity_id=str(current_user.id),
        actor_user_id=current_user.id,
    )

    db.commit()

    return get_profile(
        db,
        current_user,
    )


@router.post(
    "/addresses",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    payload: AddressCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> AddressRead:
    if payload.is_default_shipping:
        for existing in db.scalars(
            select(CustomerAddress).where(
                CustomerAddress.user_id == current_user.id,
                CustomerAddress.is_default_shipping.is_(True),
            )
        ):
            existing.is_default_shipping = False

    if payload.is_default_billing:
        for existing in db.scalars(
            select(CustomerAddress).where(
                CustomerAddress.user_id == current_user.id,
                CustomerAddress.is_default_billing.is_(True),
            )
        ):
            existing.is_default_billing = False

    address = CustomerAddress(
        user_id=current_user.id,
        **payload.model_dump(),
    )

    db.add(address)
    db.flush()

    record_audit_event(
        db,
        action="customer.address_created",
        entity_type="customer_address",
        entity_id=str(address.id),
        actor_user_id=current_user.id,
    )

    db.commit()

    return address_read(address)


@router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_address(
    address_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> None:
    address = db.scalar(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id,
            CustomerAddress.user_id == current_user.id,
        )
    )

    if address is None:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="Address not found.",
        )

    record_audit_event(
        db,
        action="customer.address_deleted",
        entity_type="customer_address",
        entity_id=str(address.id),
        actor_user_id=current_user.id,
    )

    db.delete(address)
    db.commit()
