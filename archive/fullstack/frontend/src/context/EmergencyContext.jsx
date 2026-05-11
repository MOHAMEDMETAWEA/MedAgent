import React, { createContext, useContext, useState, useEffect } from 'react';
import { getEmergencyNumber } from '../utils/emergencyNumbers';
import { useAuth } from './AuthContext';

const EmergencyContext = createContext({});

const LOCATION_CACHE_KEY = 'medagent_country_code';
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

const getCachedCountry = () => {
  try {
    const raw = localStorage.getItem(LOCATION_CACHE_KEY);
    if (!raw) return null;
    const { code, ts } = JSON.parse(raw);
    return Date.now() - ts < CACHE_TTL_MS ? code : null;
  } catch {
    return null;
  }
};

const setCachedCountry = (code) => {
  try {
    localStorage.setItem(LOCATION_CACHE_KEY, JSON.stringify({ code, ts: Date.now() }));
  } catch { /* storage full — ignore */ }
};

export function EmergencyProvider({ children }) {
  const { userData, updateUser } = useAuth();
  const contacts = userData.emergencyContacts || [];

  const [isLocating, setIsLocating] = useState(true);
  const [error, setError] = useState(null);
  const [emergencyNumber, setEmergencyNumber] = useState(null);
  const [coordinates, setCoordinates] = useState(null);

  useEffect(() => {
    determineLocation();
  }, []);

  const addContact = (newContact) => {
    updateUser({ emergencyContacts: [...contacts, newContact] });
  };

  const updateContact = (id, updatedData) => {
    const updatedContacts = contacts.map(c => c.id === id ? { ...c, ...updatedData } : c);
    updateUser({ emergencyContacts: updatedContacts });
  };

  const removeContact = (idToRemove) => {
    const updatedContacts = contacts.filter(c => c.id !== idToRemove);
    updateUser({ emergencyContacts: updatedContacts });
  };

  const determineLocation = async () => {
    setIsLocating(true);
    setError(null);

    // Serve from cache to avoid hitting rate-limited APIs on every render
    const cached = getCachedCountry();
    if (cached) {
      setEmergencyNumber(getEmergencyNumber(cached));
      setIsLocating(false);
      return;
    }

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      await fallbackToIpLocation();
      return;
    }

    try {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          setCoordinates({ lat: latitude, lon: longitude });
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), 5000);
          try {
            const response = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=3&email=medagent_app@example.com`,
              { signal: controller.signal }
            );
            clearTimeout(timer);
            if (!response.ok) throw new Error("Reverse geocoding failed");
            const data = await response.json();
            const countryCode = data.address?.country_code;
            setCachedCountry(countryCode);
            setEmergencyNumber(getEmergencyNumber(countryCode));
          } catch {
            clearTimeout(timer);
            await fallbackToIpLocation();
          } finally {
            setIsLocating(false);
          }
        },
        async () => {
          await fallbackToIpLocation();
        },
        { timeout: 10000, maximumAge: 60000 }
      );
    } catch {
      await fallbackToIpLocation();
    }
  };

  const fallbackToIpLocation = async () => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);
    try {
      const resp = await fetch('https://ipwho.is/', { signal: controller.signal });
      clearTimeout(timer);
      if (!resp.ok) throw new Error(`${resp.status}`);
      const data = await resp.json();
      if (!data.success) throw new Error('lookup failed');
      const countryCode = data.country_code?.toLowerCase();
      setCachedCountry(countryCode);
      setEmergencyNumber(getEmergencyNumber(countryCode));
    } catch {
      clearTimeout(timer);
      setEmergencyNumber('122');
    } finally {
      setIsLocating(false);
    }
  };

  const callAmbulance = () => {
    if (emergencyNumber) {
      window.location.href = `tel:${emergencyNumber}`;
    }
  };

  return (
    <EmergencyContext.Provider value={{ callAmbulance, isLocating, error, emergencyNumber, coordinates, contacts, addContact, updateContact, removeContact }}>
      {children}
    </EmergencyContext.Provider>
  );
}

export const useEmergency = () => useContext(EmergencyContext);
