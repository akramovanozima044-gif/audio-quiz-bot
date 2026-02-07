from .admin import router as admin_router
from .user import router as user_router
from .common import router as common_router
from .test import router as test_router  # ✅ YANGI

__all__ = ['admin_router', 'user_router', 'common_router']