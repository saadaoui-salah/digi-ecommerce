from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        if self.get_header(request) is None:
            token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"])
            if not token:
                return None
            validated_token = self.get_validated_token(token)
            return self.get_user(validated_token), validated_token
        return super().authenticate(request)
