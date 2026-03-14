from fastapi import APIRouter
from . import auth, clinical, system, interop, patient, governance

router = APIRouter()
# Routers will be included in main.py directly or here.
