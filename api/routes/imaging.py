"""
Imaging Router - Serving 3D volumetric data and slices.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from utils.imaging_3d import VolumetricProcessor
from api.main import oauth2_scheme # Reuse auth
import os
from config import settings

from api.main import app # Need app for some reason? No, just the router.
router = APIRouter(prefix="/imaging", tags=["Imaging"])

@router.get("/3d/{case_id}")
async def get_3d_volume(case_id: str, axis: str = "axial", slice_index: int = 0):
    """Serve a specific slice from a 3D volume."""
    # Location where DICOMs for this case are stored
    case_dir = settings.DATA_DIR / "cases" / case_id / "dicom"
    if not case_dir.exists():
        raise HTTPException(status_code=404, detail="DICOM data not found for this case")
    
    try:
        processor = VolumetricProcessor(str(case_dir))
        slice_data = processor.get_slice(axis, slice_index)
        # Convert to list for JSON (in production, use image streaming)
        return {
            "axis": axis,
            "slice_index": slice_index,
            "data": slice_data.tolist(),
            "shape": slice_data.shape
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
