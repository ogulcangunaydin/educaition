"""
Legacy routers - Kept for backward compatibility.
All routes have been migrated to app.modules.<module>.router
"""

from fastapi import APIRouter, Depends

from .dependencies import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])
router_without_auth = APIRouter()
