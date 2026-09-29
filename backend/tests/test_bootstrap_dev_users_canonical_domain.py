from app.cli.bootstrap_dev_users import CANONICAL_USERS


def test_canonical_dev_users_use_production_matching_test_domain() -> None:
    emails = [email for email, _role, _variable in CANONICAL_USERS]

    assert len(emails) == 5
    assert all(email.endswith("@dacquadolce.test") for email in emails)
    assert all("@dacqua-dolce.test" not in email for email in emails)

    assert emails == [
        "developer@dacquadolce.test",
        "admin@dacquadolce.test",
        "employee@dacquadolce.test",
        "customer@dacquadolce.test",
        "payment-test-customer@dacquadolce.test",
    ]
