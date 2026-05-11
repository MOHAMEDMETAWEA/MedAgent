import { useState, useCallback } from 'react';

/**
 * useImagePicker Hook
 * Encapsulates Gallery, Camera, and Google Drive image selection logic.
 * Returns methods to trigger each and the resulting base64 image.
 */
export function useImagePicker(onImageSelect) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [isPickerLoading, setIsPickerLoading] = useState(false);

  const handleImageResult = useCallback((base64) => {
    setSelectedImage(base64);
    if (onImageSelect) onImageSelect(base64);
  }, [onImageSelect]);

  // --- GALLERY ---
  const openGallery = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => handleImageResult(event.target.result);
        reader.readAsDataURL(file);
      }
    };
    input.click();
  }, [handleImageResult]);

  // --- CAMERA ---
  const openCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      // We return the stream so a modal can render the video preview
      return stream;
    } catch (err) {
      console.error("Camera access denied", err);
      alert("Camera access denied. Please check permissions.");
      return null;
    }
  }, []);

  // --- GOOGLE DRIVE ---
  const openDrive = useCallback(() => {
    if (!window.google || !window.gapi) {
      alert("Google Services not loaded yet. Please wait a moment.");
      return;
    }

    const API_KEY = import.meta.env.VITE_GOOGLE_API_KEY;
    const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    if (!API_KEY || !CLIENT_ID) {
      console.error("Google API Keys missing in .env");
      alert("Drive integration not configured.");
      return;
    }

    const tokenClient = window.google.accounts.oauth2.initTokenClient({
      client_id: CLIENT_ID,
      scope: 'https://www.googleapis.com/auth/drive.readonly',
      callback: (response) => {
        if (response.error !== undefined) {
          console.error("Auth error", response);
          return;
        }
        createPicker(response.access_token);
      },
    });

    const createPicker = (accessToken) => {
      const view = new window.google.picker.View(window.google.picker.ViewId.DOCS_IMAGES);
      const picker = new window.google.picker.PickerBuilder()
        .enableFeature(window.google.picker.Feature.NAV_HIDDEN)
        .setAppId(CLIENT_ID)
        .setOAuthToken(accessToken)
        .addView(view)
        .setCallback(async (data) => {
          if (data.action === window.google.picker.Action.PICKED) {
            const fileId = data.docs[0].id;
            setIsPickerLoading(true);
            try {
              // Fetch file blob via Drive API
              const res = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`, {
                headers: { Authorization: `Bearer ${accessToken}` }
              });
              const blob = await res.blob();
              const reader = new FileReader();
              reader.onload = (e) => {
                handleImageResult(e.target.result);
                setIsPickerLoading(false);
              };
              reader.readAsDataURL(blob);
            } catch (err) {
              console.error("Failed to fetch Drive image", err);
              setIsPickerLoading(false);
            }
          }
        })
        .build();
      picker.setVisible(true);
    };

    tokenClient.requestAccessToken({ prompt: 'consent' });
  }, [handleImageResult]);

  return {
    selectedImage,
    isPickerLoading,
    openGallery,
    openCamera,
    openDrive,
    resetImage: () => setSelectedImage(null)
  };
}
