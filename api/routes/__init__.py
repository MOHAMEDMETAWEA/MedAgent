from fastapi import APIRouter

from . import auth, clinical, feedback, governance, imaging, patient, system

router = APIRouter()
# Routers will be included in main.py directly or here.
