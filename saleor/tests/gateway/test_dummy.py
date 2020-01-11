from decimal import Decimal

import pytest

from saleor.payment import (
    ChargeStatus,
    PaymentError,
    TransactionKind,
    get_payment_gateway,
)
from saleor.payment.utils import (
    create_payment_information,
    gateway_authorize,
    gateway_capture,
    gateway_process_payment,
    gateway_refund,
    gateway_void,
)


def test_authorize_success(payment_dummy):
    txn = gateway_authorize(payment=payment_dummy, payment_token="Fake")
    assert txn.is_success
    assert txn.kind == TransactionKind.AUTH
    assert txn.payment == payment_dummy
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active


@pytest.mark.parametrize(
    "is_active, charge_status",
    [
        (False, ChargeStatus.NOT_CHARGED),
        (False, ChargeStatus.PARTIALLY_CHARGED),
        (False, ChargeStatus.FULLY_CHARGED),
        (False, ChargeStatus.PARTIALLY_REFUNDED),
        (False, ChargeStatus.FULLY_REFUNDED),
        (True, ChargeStatus.PARTIALLY_CHARGED),
        (True, ChargeStatus.FULLY_CHARGED),
        (True, ChargeStatus.PARTIALLY_REFUNDED),
        (True, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_authorize_failed(is_active, charge_status, payment_dummy):
    payment = payment_dummy
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway_authorize(payment=payment, payment_token="Fake")
        assert txn is None


def test_authorize_gateway_error(payment_dummy, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    with pytest.raises(PaymentError):
        txn = gateway_authorize(payment=payment_dummy, payment_token="Fake")
        assert txn.kind == TransactionKind.AUTH
        assert not txn.is_success
        assert txn.payment == payment_dummy


def test_void_success(payment_txn_preauth):
    assert payment_txn_preauth.is_active
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    txn = gateway_void(payment=payment_txn_preauth)
    assert txn.is_success
    assert txn.kind == TransactionKind.VOID
    assert txn.payment == payment_txn_preauth
    payment_txn_preauth.refresh_from_db()
    assert not payment_txn_preauth.is_active
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED


@pytest.mark.parametrize(
    "is_active, charge_status",
    [
        (False, ChargeStatus.NOT_CHARGED),
        (False, ChargeStatus.PARTIALLY_CHARGED),
        (False, ChargeStatus.FULLY_CHARGED),
        (False, ChargeStatus.PARTIALLY_REFUNDED),
        (False, ChargeStatus.FULLY_REFUNDED),
        (True, ChargeStatus.PARTIALLY_CHARGED),
        (True, ChargeStatus.FULLY_CHARGED),
        (True, ChargeStatus.PARTIALLY_REFUNDED),
        (True, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_void_failed(is_active, charge_status, payment_dummy):
    payment = payment_dummy
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway_void(payment=payment)
        assert txn is None


def test_void_gateway_error(payment_txn_preauth, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    with pytest.raises(PaymentError):
        txn = gateway_void(payment=payment_txn_preauth)
        assert txn.kind == TransactionKind.VOID
        assert not txn.is_success
        assert txn.payment == payment_txn_preauth


@pytest.mark.parametrize(
    "amount, charge_status",
    [("98.40", ChargeStatus.FULLY_CHARGED), (70, ChargeStatus.PARTIALLY_CHARGED)],
)
def test_capture_success(amount, charge_status, payment_txn_preauth):
    txn = gateway_capture(payment=payment_txn_preauth, amount=Decimal(amount))
    assert txn.is_success
    assert txn.payment == payment_txn_preauth
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == charge_status
    assert payment_txn_preauth.is_active


@pytest.mark.parametrize(
    "amount, captured_amount, charge_status, is_active",
    [
        (80, 0, ChargeStatus.NOT_CHARGED, False),
        (120, 0, ChargeStatus.NOT_CHARGED, True),
        (80, 20, ChargeStatus.PARTIALLY_CHARGED, True),
        (80, 80, ChargeStatus.FULLY_CHARGED, True),
        (80, 0, ChargeStatus.FULLY_REFUNDED, True),
    ],
)
def test_capture_failed(
    amount, captured_amount, charge_status, is_active, payment_dummy
):
    payment = payment_dummy
    payment.is_active = is_active
    payment.captured_amount = captured_amount
    payment.charge_status = charge_status
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway_capture(payment=payment, amount=amount)
        assert txn is None


def test_capture_gateway_error(payment_txn_preauth, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    with pytest.raises(PaymentError):
        txn = gateway_capture(payment=payment_txn_preauth, amount=80)
        assert txn.kind == TransactionKind.CAPTURE
        assert not txn.is_success
        assert txn.payment == payment_txn_preauth


@pytest.mark.parametrize(
    (
        "initial_captured_amount, refund_amount, final_captured_amount, "
        "final_charge_status, active_after"
    ),
    [
        (80, 80, 0, ChargeStatus.FULLY_REFUNDED, False),
        (80, 10, 70, ChargeStatus.PARTIALLY_REFUNDED, True),
    ],
)
def test_refund_success(
    initial_captured_amount,
    refund_amount,
    final_captured_amount,
    final_charge_status,
    active_after,
    payment_txn_captured,
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = initial_captured_amount
    payment.save()
    txn = gateway_refund(payment=payment, amount=Decimal(refund_amount))
    assert txn.kind == TransactionKind.REFUND
    assert txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == final_charge_status
    assert payment.captured_amount == final_captured_amount
    assert payment.is_active == active_after


@pytest.mark.parametrize(
    "initial_captured_amount, refund_amount, initial_charge_status",
    [
        (0, 10, ChargeStatus.NOT_CHARGED),
        (10, 20, ChargeStatus.PARTIALLY_CHARGED),
        (10, 20, ChargeStatus.FULLY_CHARGED),
        (10, 20, ChargeStatus.PARTIALLY_REFUNDED),
        (80, 0, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_refund_failed(
    initial_captured_amount, refund_amount, initial_charge_status, payment_dummy
):
    payment = payment_dummy
    payment.charge_status = initial_charge_status
    payment.captured_amount = Decimal(initial_captured_amount)
    payment.save()
    with pytest.raises(PaymentError):
        txn = gateway_refund(payment=payment, amount=Decimal(refund_amount))
        assert txn is None


def test_refund_gateway_error(payment_txn_captured, monkeypatch):
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = Decimal("80.00")
    payment.save()
    with pytest.raises(PaymentError):
        gateway_refund(payment=payment, amount=Decimal("80.00"))

    payment.refresh_from_db()
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.captured_amount == Decimal("80.00")


@pytest.mark.parametrize(
    "kind, charge_status",
    (
        (TransactionKind.AUTH, ChargeStatus.NOT_CHARGED),
        (TransactionKind.CAPTURE, ChargeStatus.FULLY_CHARGED),
        (TransactionKind.REFUND, ChargeStatus.FULLY_REFUNDED),
    ),
)
def test_dummy_payment_form(kind, charge_status, payment_dummy):
    payment = payment_dummy
    data = {"charge_status": charge_status}
    payment_gateway, gateway_config = get_payment_gateway(payment.gateway)
    payment_info = create_payment_information(payment)

    form = payment_gateway.create_form(
        data=data,
        payment_information=payment_info,
        connection_params=gateway_config.connection_params,
    )
    assert form.is_valid()
    gateway_process_payment(payment=payment, payment_token=form.get_payment_token())
    payment.refresh_from_db()
    assert payment.transactions.last().kind == kind
