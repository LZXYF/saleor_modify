import uuid

from ... import ChargeStatus, TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData
from .forms import DummyPaymentForm


def dummy_success():
    return True


def get_client_token(**_):
    return str(uuid.uuid4())


def create_form(data, payment_information, connection_params):
    return DummyPaymentForm(data=data)


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    success = dummy_success()
    error = None
    if not success:
        error = "Unable to authorize transaction"
    return GatewayResponse(
        is_success=success,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    error = None
    success = dummy_success()
    if not success:
        error = "Unable to void the transaction."
    return GatewayResponse(
        is_success=success,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform capture transaction."""
    error = None
    success = dummy_success()
    if not success:
        error = "Unable to process capture"

    return GatewayResponse(
        is_success=success,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    error = None
    success = dummy_success()
    if not success:
        error = "Unable to process refund"
    return GatewayResponse(
        is_success=success,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process the payment."""
    token = payment_information.token

    # Process payment normally if payment token is valid
    if token not in dict(ChargeStatus.CHOICES):
        return capture(payment_information, config)

    # Process payment by charge status which is selected in the payment form
    # Note that is for testing by dummy gateway only
    charge_status = token
    authorize_response = authorize(payment_information, config)
    if charge_status == ChargeStatus.NOT_CHARGED:
        return authorize_response

    if not config.auto_capture:
        return authorize_response

    capture_response = capture(payment_information, config)
    if charge_status == ChargeStatus.FULLY_REFUNDED:
        return refund(payment_information, config)
    return capture_response
