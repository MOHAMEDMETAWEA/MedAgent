import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../services/apiClient';

const AuthContext = createContext({});

/** Only send a real GUID; URLs or junk values break System.Text.Json Guid binding. */
function normalizeProfileImageIdForApi(value) {
  if (value == null || value === '') return null;
  const s = String(value).trim();
  const uuid =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (uuid.test(s)) return s;
  const m = s.match(
    /\/api\/photos\/content\/([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/i
  );
  return m ? m[1] : null;
}

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem('medagent_token');
        if (!token) {
          setIsAuthenticated(false);
          setLoading(false);
          return;
        }

        // Fetch the full Medical ID (includes profile, insurance, contacts)
        const response = await apiClient.get('/medical-id');
        // Handle PascalCase or camelCase from backend
        const cloudData = response.data.User || response.data.user || response.data;
        
        // --- Migration Logic: Sync Local to Cloud ---
        const localData = JSON.parse(localStorage.getItem('medagent_user_data') || '{}');
        const localContacts = JSON.parse(localStorage.getItem(`medagent_emergency_contacts_${localData.email || 'Guest'}`) || '[]');
        
        // Accurate detection of "Empty Cloud Profile" vs "Existing Profile"
        const isCloudEmpty = (!cloudData.nationalId || cloudData.nationalId === "") && 
                           (!cloudData.bloodType || cloudData.bloodType === "Unknown") && 
                           (cloudData.emergencyContacts?.length === 0);

        const hasLocalData = localData.nationalId || 
                           (localData.allergies?.length > 0) || 
                           (localData.insuranceData?.providerName) ||
                           (localContacts.length > 0);

        let finalData = cloudData;

        if (isCloudEmpty && hasLocalData) {
          console.log("Migrating substantial local data to new cloud profile...");
          try {
            const migrationPayload = {
              ...cloudData,
              ...localData,
              bloodType: localData.bloodType || "Unknown",
              insurance: localData.insurance || localData.insuranceData || {},
              emergencyContacts: localContacts
            };
            
            await apiClient.put('/medical-id', migrationPayload);
            finalData = migrationPayload;
          } catch (syncError) {
            console.error("Migration failed", syncError);
          }
        }

        // --- Profile Image Handling ---
        let profileImageUrl = localData.profileImage;
        // If the backend has a specific photo ID designated for the profile, use it
        if (finalData.profileImageId) {
          profileImageUrl = `/api/photos/content/${finalData.profileImageId}`;
        }

        setUserData(prev => {
          const updated = {
            ...prev,
            ...finalData,
            profileImage: profileImageUrl,
            profileImageId: finalData.profileImageId || prev.profileImageId,
            isRegistered: true,
          };
          localStorage.setItem('medagent_user_data', JSON.stringify(updated));
          return updated;
        });
        setIsAuthenticated(true);
      } catch (error) {
        console.error("Auth status verification failed", error);
        localStorage.removeItem('medagent_token');
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const [userData, setUserData] = useState(() => {
    const savedData = localStorage.getItem('medagent_user_data');
    if (savedData) {
      try {
        return JSON.parse(savedData);
      } catch (e) {
        console.error("Failed to parse saved user data", e);
      }
    }
    return {
      firstName: '',
      lastName: '',
      email: '',
      profileImage: null,
      profileImageId: null,
      patientId: '#NEW-882-902',
      bloodType: 'Unknown',
      weight: '',
      height: '',
      gender: 'M',
      nationalId: '',
      allergies: [],
      prescriptions: [],
      chronicConditions: [],
      organDonor: '',
      advanceDirectives: '',
      lastVerified: '-',
      emergencyAccessibility: 'In the event of an emergency, medical professionals can access your vital data using the QR code on your MedAgent physical card or via the secure emergency bypass on your smartphone lock screen. Your data is encrypted and access is logged for your security.',
      insurance: {
        providerName: '',
        memberId: '',
        groupNumber: '',
        planType: '',
        cardImage: null
      },
      emergencyContacts: [],
      scanHistory: [],
      isRegistered: false
    };
  });

  // Persist userData to localStorage (as cache)
  useEffect(() => {
    localStorage.setItem('medagent_user_data', JSON.stringify(userData));
  }, [userData]);

  const updateUser = async (newData) => {
    const previous = userData;
    const updated = { ...userData, ...newData };

    // Optimistically update local state
    setUserData(updated);

    // Persist batch update to backend
    const token = localStorage.getItem('medagent_token');
    if (token) {
      try {

        // --- SURGICAL DTO MAPPING ---
        // We MUST strip 'id' fields from collections because the backend DTOs (AllergyDto, etc.) 
        // do not have them, and sending unknown properties causes a 400 Bad Request.
        const cleanAllergies = (updated.allergies || []).map(({ id, ...rest }) => ({
          name: rest.name || "",
          severity: rest.severity || "Mild"
        }));
        
        const cleanConditions = (updated.chronicConditions || []).map(({ id, ...rest }) => ({
          name: rest.name || "",
          description: rest.description || ""
        }));
        
        const cleanPrescriptions = (updated.prescriptions || []).map(({ id, ...rest }) => ({
          name: rest.name || "",
          freq: rest.freq || "",
          time: rest.time || ""
        }));

        const cleanContacts = (updated.emergencyContacts || []).map(({ id, ...rest }) => ({
          name: rest.name || "",
          phone: rest.phone || "",
          relation: rest.relation || "",
          avatar: rest.avatar || "",
          type: rest.type || "family",
          id: (id && id.toString().includes('-')) ? id : null // Only keep if it's a GUID (contains hyphen)
        }));

        const payload = {
          firstName: updated.firstName || userData.firstName || "",
          lastName: updated.lastName || userData.lastName || "",
          email: updated.email || userData.email || "",
          patientId: updated.patientId || userData.patientId || "",
          bloodType: updated.bloodType || "Unknown",
          gender: updated.gender || "M",
          profileImageId: normalizeProfileImageIdForApi(updated.profileImageId ?? userData.profileImageId),
          weight: String(updated.weight || ""),
          height: String(updated.height || ""),
          nationalId: updated.nationalId || "",
          organDonor: updated.organDonor || "",
          advanceDirectives: updated.advanceDirectives || "",
          allergies: cleanAllergies,
          chronicConditions: cleanConditions,
          prescriptions: cleanPrescriptions,
          insurance: {
            providerName: updated.insurance?.providerName || "",
            memberId: updated.insurance?.memberId || "",
            groupNumber: updated.insurance?.groupNumber || "",
            planType: updated.insurance?.planType || "",
            cardImage: updated.insurance?.cardImage || ""
          },
          emergencyContacts: cleanContacts
        };
        
        await apiClient.put('/medical-id', payload);
      } catch (error) {
        console.error("Failed to sync batch update to backend", error.response?.data ?? error.message);
        setUserData(previous);
      }
    }
  };

  const login = async (token, userProfile) => {
    localStorage.setItem('medagent_token', token);
    setIsAuthenticated(true);

    // Always fetch the full medical profile so allergies, conditions,
    // prescriptions, insurance, and contacts are present immediately —
    // the login response only contains basic identity fields.
    try {
      const response = await apiClient.get('/medical-id');
      const cloudData = response.data;

      const profileImageUrl = cloudData.profileImageId
        ? `/api/photos/content/${cloudData.profileImageId}`
        : (userProfile?.profileImage ?? null);

      setUserData(prev => {
        const updated = {
          ...prev,
          ...cloudData,
          profileImage: profileImageUrl,
          profileImageId: cloudData.profileImageId || prev.profileImageId,
          isRegistered: true,
        };
        localStorage.setItem('medagent_user_data', JSON.stringify(updated));
        return updated;
      });
    } catch {
      // /medical-id unreachable — fall back to the basic profile from the
      // login response so the user is at least authenticated.
      if (userProfile) {
        const profileImageUrl = userProfile.profileImageId
          ? `/api/photos/content/${userProfile.profileImageId}`
          : userProfile.profileImage ?? null;

        setUserData(prev => {
          const updated = {
            ...prev,
            ...userProfile,
            profileImage: profileImageUrl,
            profileImageId: userProfile.profileImageId || prev.profileImageId,
            isRegistered: true,
          };
          localStorage.setItem('medagent_user_data', JSON.stringify(updated));
          return updated;
        });
      }
    }
  };

  const logout = () => {
    localStorage.removeItem('medagent_token');
    localStorage.removeItem('medagent_user_data');
    setIsAuthenticated(false);
    setUserData({
      firstName: '',
      lastName: '',
      email: '',
      profileImage: null,
      patientId: '#NEW-882-902',
      bloodType: '',
      weight: '',
      height: '',
      gender: 'M',
      nationalId: '',
      allergies: [],
      prescriptions: [],
      chronicConditions: [],
      organDonor: '',
      advanceDirectives: '',
      lastVerified: '-',
      emergencyAccessibility: 'In the event of an emergency, medical professionals can access your vital data using the QR code on your MedAgent physical card or via the secure emergency bypass on your smartphone lock screen. Your data is encrypted and access is logged for your security.',
      insurance: {
        providerName: '',
        memberId: '',
        groupNumber: '',
        planType: '',
        cardImage: null
      },
      isRegistered: false
    });
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading, login, logout, userData, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
