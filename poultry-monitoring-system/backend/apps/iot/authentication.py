"""Device bearer-token authentication for the ingestion API.

A device authenticates with header ``Authorization: Device <raw-token>``.
The raw token is hashed and matched against ``DeviceToken.key_hash``; the
authenticated "user" is an unauthenticated ``AnonymousUser`` with the device
attached at ``request.auth`` and ``request.device``.
"""
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from rest_framework import authentication, exceptions

from .models import DeviceToken, hash_token


class DeviceUser(AnonymousUser):
    """An anonymous principal that nonetheless carries the device identity."""

    def __init__(self, device):
        super().__init__()
        self.device = device

    @property
    def is_authenticated(self):  # DRF treats this as an authenticated principal
        return True

    def __str__(self):
        return f"device:{self.device.device_id}"


class DeviceTokenAuthentication(authentication.BaseAuthentication):
    keyword = "Device"

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth) != 2:
            raise exceptions.AuthenticationFailed("Invalid device token header.")
        raw = auth[1].decode()
        try:
            token = DeviceToken.objects.select_related("device").get(
                key_hash=hash_token(raw), is_active=True
            )
        except DeviceToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid or revoked device token.")
        if token.device.status == token.device.Status.DECOMMISSIONED:
            raise exceptions.AuthenticationFailed("Device is decommissioned.")

        DeviceToken.objects.filter(pk=token.pk).update(last_used_at=timezone.now())
        request.device = token.device
        return (DeviceUser(token.device), token)

    def authenticate_header(self, request):
        return self.keyword
