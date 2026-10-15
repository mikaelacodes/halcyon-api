from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extends the built-in User with the role our permission classes check."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STANDARD = "STANDARD", "Standard User"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STANDARD)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["role"])]

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
