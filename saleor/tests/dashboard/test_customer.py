import json
from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.templatetags.static import static
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from saleor.account import events as account_events
from saleor.account.models import CustomerNote, User
from saleor.core.utils import build_absolute_uri
from saleor.dashboard.customer.forms import (
    CustomerDeleteForm,
    CustomerForm,
    CustomerNoteForm,
)
from saleor.settings import DEFAULT_FROM_EMAIL


def test_ajax_users_list(admin_client, admin_user, customer_user):
    users = sorted([admin_user, customer_user], key=lambda user: user.email)
    users_list = [{"id": user.pk, "text": user.get_ajax_label()} for user in users]

    url = reverse("dashboard:ajax-users-list")
    response = admin_client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    resp_decoded = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 200
    assert resp_decoded == {"results": users_list}


def test_customers_list(admin_client):
    response = admin_client.get(reverse("dashboard:customers"))
    assert response.status_code == 200


def test_customer_detail_view(admin_client, customer_user):
    response = admin_client.get(
        reverse("dashboard:customer-details", args=[customer_user.pk])
    )
    assert response.status_code == 200


def test_customer_create(admin_client):
    response = admin_client.get(reverse("dashboard:customer-create"))
    assert response.status_code == 200


def test_view_customer_create(admin_client):
    url = reverse("dashboard:customer-create")
    response = admin_client.post(url, data={"email": "customer01@example.com"})
    assert response.status_code == 302
    assert User.objects.filter(email="customer01@example.com").exists()


def test_add_customer_form(staff_user):
    user_count = User.objects.count()
    customer_form = CustomerForm({"email": "customer01@example.com"}, user=staff_user)
    customer_form.is_valid()
    new_customer = customer_form.save()
    assert User.objects.count() == user_count + 1

    event = account_events.CustomerEvent.objects.get()
    assert event.type == account_events.CustomerEvents.ACCOUNT_CREATED
    assert event.user == new_customer


def test_edit_customer_form(customer_user, staff_user):
    customer = customer_user
    customer_form = CustomerForm(
        {"first_name": "Jan", "last_name": "Nowak", "email": customer.email},
        instance=customer,
        user=staff_user,
    )
    customer_form.is_valid()
    customer_form.save()
    customer.refresh_from_db()
    assert customer.first_name == "Jan"
    assert customer.last_name == "Nowak"

    event = account_events.CustomerEvent.objects.get()
    assert event.type == account_events.CustomerEvents.NAME_ASSIGNED
    assert event.user == staff_user
    assert event.parameters == {"message": customer.get_full_name()}


def test_edit_customer_form_new_email_generates_event(customer_user, staff_user):
    customer = customer_user
    customer_form = CustomerForm(
        {
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": "hello@example.com",
        },
        instance=customer,
        user=staff_user,
    )
    customer_form.is_valid()
    customer_form.save()
    customer.refresh_from_db()
    assert customer.email == "hello@example.com"

    event = account_events.CustomerEvent.objects.get()
    assert event.type == account_events.CustomerEvents.EMAIL_ASSIGNED
    assert event.user == staff_user
    assert event.parameters == {"message": customer.email}


def test_edit_customer_form_no_changes_generates_no_event(customer_user, staff_user):
    customer = customer_user
    customer_form = CustomerForm(
        {
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
        },
        instance=customer,
        user=staff_user,
    )
    customer_form.is_valid()
    customer_form.save()
    assert not account_events.CustomerEvent.objects.exists()


def test_add_note_to_customer(admin_user, customer_user):
    customer = customer_user
    note = CustomerNote(customer=customer, user=admin_user)
    note_form = CustomerNoteForm({"content": "test_note"}, instance=note)
    note_form.is_valid()
    note_form.save()
    assert customer.notes.first().content == "test_note"
    event = account_events.CustomerEvent.objects.get()
    assert event.type == account_events.CustomerEvents.NOTE_ADDED
    assert event.user == note.customer
    assert event.parameters == {"message": "test_note"}


def test_update_customer_note_generates_no_event(admin_user, customer_user):
    note = CustomerNote(customer=customer_user, user=admin_user)
    note.save()

    note_form = CustomerNoteForm({"content": "hello world note"}, instance=note)
    note_form.is_valid()
    note_form.save()

    assert customer_user.notes.first().content == "hello world note"
    assert not account_events.CustomerEvent.objects.exists()


def test_add_note_to_customer_from_url(admin_client, customer_user):
    customer = customer_user
    assert customer.notes.count() == 0
    data = {"user": admin_client, "customer": customer, "content": "test_note"}
    url = reverse("dashboard:customer-add-note", kwargs={"customer_pk": customer.pk})
    response = admin_client.post(url, data)

    assert response.status_code == 200


def test_view_delete_customer(admin_client, admin_user, customer_user):
    url = reverse("dashboard:customer-delete", args=[admin_user.pk])
    response = admin_client.post(url, data={"csrf": "exampledata"})
    assert response.status_code == 400

    url = reverse("dashboard:customer-delete", args=[customer_user.pk])
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, data={"csrf": "exampledata"})
    assert not User.objects.filter(pk=customer_user.pk).exists()
    assert response.status_code == 302


@patch(
    "saleor.dashboard.customer.views.account_events"
    ".staff_user_deleted_a_customer_event"
)
def test_deleting_a_customer_generates_an_event(
    mocked_deletion_event, admin_client, admin_user, customer_user
):
    """Deleting a customer as a staff admin should generate an event
    and this event should remain anonymous as a customer point of view (GDPR)."""

    url = reverse("dashboard:customer-delete", args=[customer_user.pk])
    response = admin_client.post(url, data={"csrf": "exampledata"})
    assert response.status_code == 302

    # Ensure the customer was properly deleted
    # and any related event was properly triggered
    mocked_deletion_event.assert_called_once_with(staff_user=admin_user)


def test_form_delete_customer(
    staff_user, customer_user, admin_user, permission_manage_staff
):
    # Deleting a customer with valid data should be valid
    data = {"csrf": "example-data"}
    form = CustomerDeleteForm(data, instance=customer_user, user=staff_user)
    assert form.is_valid()

    # Deleting your own account is not allowed
    form = CustomerDeleteForm(data, instance=staff_user, user=staff_user)
    assert not form.is_valid()

    # Deleting a superuser is not allowed
    form = CustomerDeleteForm(data, instance=admin_user, user=staff_user)
    assert not form.is_valid()

    # Deleting another staff is not allowed without relevant permissions
    another_staff_user = User.objects.create(is_staff=True, email="exa@mp.le")
    form = CustomerDeleteForm(data, instance=another_staff_user, user=staff_user)
    assert not form.is_valid()

    # Deleting another staff user is allowed with relevant permissions
    staff_user.user_permissions.add(permission_manage_staff)
    staff_user = User.objects.get(pk=staff_user.pk)
    form = CustomerDeleteForm({}, instance=another_staff_user, user=staff_user)
    assert form.is_valid()


def test_add_customer_and_set_password(admin_client):
    url = reverse("dashboard:customer-create")
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "is_active": True,
    }
    response = admin_client.post(url, data)
    assert response.status_code == 302
    new_user = User.objects.get(email=data["email"])
    assert new_user.first_name == data["first_name"]
    assert new_user.last_name == data["last_name"]
    assert not new_user.password
    uid = urlsafe_base64_encode(force_bytes(new_user.pk))
    token = default_token_generator.make_token(new_user)
    response = admin_client.get(
        reverse(
            "account:reset-password-confirm", kwargs={"uidb64": uid, "token": token}
        )
    )
    assert response.status_code == 302
    post_data = {"new_password1": "password", "new_password2": "password"}
    response = admin_client.post(response["Location"], post_data)
    assert response.status_code == 302
    assert response["Location"] == reverse("account:reset-password-complete")
    new_user = User.objects.get(email=data["email"])
    assert new_user.has_usable_password()

    # Retrieve the events and ensure it was properly generated
    account_creation_event, password_reset_email_sent_event = (
        account_events.CustomerEvent.objects.all()
    )
    assert account_creation_event.type == account_events.CustomerEvents.ACCOUNT_CREATED
    assert account_creation_event.user.pk == new_user.pk
    assert (
        password_reset_email_sent_event.type
        == account_events.CustomerEvents.PASSWORD_RESET
    )
    assert password_reset_email_sent_event.user.pk == new_user.pk


def test_send_set_password_customer_email(customer_user, site_settings):
    site = site_settings.site
    uid = urlsafe_base64_encode(force_bytes(customer_user.pk))
    token = default_token_generator.make_token(customer_user)
    logo_url = build_absolute_uri(static("images/logo-light.svg"))
    password_set_url = build_absolute_uri(
        reverse(
            "account:reset-password-confirm", kwargs={"token": token, "uidb64": uid}
        )
    )
    ctx = {
        "logo_url": logo_url,
        "password_set_url": password_set_url,
        "site_name": site.name,
    }
    send_templated_mail(
        template_name="dashboard/customer/set_password",
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[customer_user.email],
        context=ctx,
    )
    assert len(mail.outbox) == 1
    sended_message = mail.outbox[0].body
    assert password_set_url in sended_message
