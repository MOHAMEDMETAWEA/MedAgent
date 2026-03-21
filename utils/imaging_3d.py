"""
Volumetric Processing Engine for 3D Medical Imaging.
Converts DICOM series into volumetric arrays for 3D rendering.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pydicom

logger = logging.getLogger(__name__)


class VolumetricProcessor:
    def __init__(self, dicom_dir: str):
        self.dicom_dir = Path(dicom_dir)
        self.volume = None
        self.pixel_spacing = None
        self.slice_thickness = None

    def load_series(self) -> Tuple[np.ndarray, Dict]:
        """Load a series of DICOM files into a 3D volume."""
        dicom_files = [f for f in self.dicom_dir.glob("*.dcm")]
        if not dicom_files:
            logger.error(f"No DICOM files found in {self.dicom_dir}")
            raise FileNotFoundError("Empty DICOM directory")

        # Sort by Instance Number or Image Position Patient
        slices = [pydicom.dcmread(f) for f in dicom_files]
        slices.sort(
            key=lambda x: int(x.InstanceNumber) if hasattr(x, "InstanceNumber") else 0
        )

        # Extract spacing
        self.pixel_spacing = (
            slices[0].PixelSpacing if hasattr(slices[0], "PixelSpacing") else [1.0, 1.0]
        )
        self.slice_thickness = (
            slices[0].SliceThickness if hasattr(slices[0], "SliceThickness") else 1.0
        )

        # Build volume
        img_shape = list(slices[0].pixel_array.shape)
        img_shape.append(len(slices))
        self.volume = np.zeros(img_shape, dtype=slices[0].pixel_array.dtype)

        for i, s in enumerate(slices):
            self.volume[:, :, i] = s.pixel_array

        logger.info(f"Loaded volume with shape: {self.volume.shape}")
        return self.volume, {
            "spacing": self.pixel_spacing,
            "thickness": self.slice_thickness,
            "shape": self.volume.shape,
        }

    def get_slice(self, axis: str, index: int) -> np.ndarray:
        """Get a single slice along axial (z), coronal (y), or sagittal (x) planes."""
        if self.volume is None:
            self.load_series()

        if axis == "axial":
            return self.volume[:, :, index]
        elif axis == "coronal":
            return self.volume[:, index, :]
        elif axis == "sagittal":
            return self.volume[index, :, :]
        else:
            raise ValueError("Invalid axis. Choose axial, coronal, or sagittal.")

    def apply_window_level(
        self, image: np.ndarray, window: float, level: float
    ) -> np.ndarray:
        """Apply Window/Level (Brightness/Contrast) for clinical display."""
        img_min = level - window // 2
        img_max = level + window // 2
        windowed = np.clip(image, img_min, img_max)
        return ((windowed - img_min) / (img_max - img_min) * 255.0).astype(np.uint8)
