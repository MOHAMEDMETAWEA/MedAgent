from fastapi import APIRouter
from . import auth, clinical, system, patient, governance, feedback, imaging

router = APIRouter()
# Routers will be included in main.py directly or here.
