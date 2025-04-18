from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    """Custom authentication backend to authenticate users with email instead of username."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)  # Use email as the identifier
            if user.check_password(password):  # Check the password
                return user
        except User.DoesNotExist:
            return None

