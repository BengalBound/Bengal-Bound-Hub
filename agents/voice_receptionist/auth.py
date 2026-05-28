"""
DRF authentication for the Voice Receptionist agent.
Uses Django session auth and syncs the VR-specific UserProfile on each request.
"""
from rest_framework.authentication import SessionAuthentication


class FirebaseAuthentication(SessionAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, _ = result
        self._sync_voice_profile(user)
        return (user, None)

    @staticmethod
    def _sync_voice_profile(user):
        from agents.voice_receptionist.models import UserProfile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "firebase_uid": getattr(user, "firebase_uid", None) or user.username,
                "role": "staff",
            },
        )
