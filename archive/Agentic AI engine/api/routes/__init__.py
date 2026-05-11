from fastapi import APIRouter

from . import (analytics, auth, clinical, feedback, governance, imaging,
               medications, patient, system)

router = APIRouter()
# Routers will be included in main.py directly or here.
