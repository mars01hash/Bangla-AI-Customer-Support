import os
from app.config import settings

print("ADMIN_INITIAL_PASSWORD:", repr(settings.ADMIN_INITIAL_PASSWORD))
print("Length:", len(settings.ADMIN_INITIAL_PASSWORD))
print("Type:", type(settings.ADMIN_INITIAL_PASSWORD))
print("JWT_SECRET:", repr(settings.JWT_SECRET))
