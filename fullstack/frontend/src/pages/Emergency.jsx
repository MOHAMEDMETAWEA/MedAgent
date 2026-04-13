import React, { useState, useEffect, useRef } from 'react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { ActivitySquare, PhoneCall, AlertOctagon, Navigation2, Copy, Ambulance, Phone, Contact2, Share2, LocateFixed, Loader2, Send, Droplet } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useHealthData } from '../controllers/useHealthData';
import { PageHeader } from '../components/ui/PageHeader';
import { DataState } from '../components/ui/DataState';
import { AIService } from '../services/api/aiService';
import { useEmergency } from '../context/EmergencyContext';
import { useLongPress } from '../hooks/useLongPress';
import { playSiren } from '../utils/audio';
import { EmergencyContactsList } from '../components/contact/EmergencyContactsList';
import { useLocationServices } from '../hooks/useLocationServices';
import { useAuth } from '../context/AuthContext';
import { FirstAidModal } from '../components/emergency/FirstAidModal';
import { DigitalInsuranceCard } from '../components/medical/DigitalInsuranceCard';

export default function Emergency() {
  const { t } = useTranslation();
  const { userData } = useAuth();
  const { data: emergencyFacilities, loading, error } = useHealthData(AIService.getEmergencyFacilities);
  const { callAmbulance, isLocating, emergencyNumber, coordinates } = useEmergency();
  const { location, address, nearestHospital, loading: locLoading } = useLocationServices();

  useEffect(() => {
    if (nearestHospital) {
      console.log("MedAgent UI: Nearest Hospital Updated:", nearestHospital);
    }
  }, [nearestHospital]);
  
  const [smsSent, setSmsSent] = useState(false);
  const [isSirenActive, setIsSirenActive] = useState(false);
  const [isFirstAidModalOpen, setIsFirstAidModalOpen] = useState(false);
  const [isCardViewOpen, setIsCardViewOpen] = useState(false);
  const stopSirenRef = useRef(null);

  const handleCopyLink = () => {
    if (location) {
      const url = `https://www.google.com/maps?q=${location.lat},${location.lng}`;
      navigator.clipboard.writeText(url).then(() => {
        alert('Location link copied to clipboard!');
      });
    }
  };

  const displayFacilities = nearestHospital && emergencyFacilities
    ? [nearestHospital, ...emergencyFacilities.slice(1)]
    : emergencyFacilities || [];

  // Trigger siren and SMS when held for 5 seconds
  const handleLongPress = async () => {
    stopSirenRef.current = playSiren();
    setIsSirenActive(true);
    setSmsSent(true);

    try {
      // Native SMS Intent Delivery using user Contacts
      const contactsData = userData.emergencyContacts || [];
      const contactNumbers = contactsData.map(c => c.phone.replace(/[^0-9+]/g, '')).join(',');
      
      const locationStr = coordinates ? `https://maps.google.com/?q=${coordinates.lat},${coordinates.lon}` : "Location not resolved yet";
      
      // Simulating the Apple iOS SOS message text pattern
      const sosMessage = `Emergency SOS. I have called for emergency services. You are receiving this message because you are listed as my emergency contact. My current location is: ${locationStr}`;
      
      // Try to open the device's native SMS application with pre-filled body
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
      const smsUrl = `sms:${contactNumbers}${isIOS ? '&' : '?'}body=${encodeURIComponent(sosMessage)}`;
      
      // Execute Native Intent via invisible anchor block or direct location change
      window.location.href = smsUrl;
    } catch (e) {
      console.error("Failed to generate SMS dispatch.", e);
    }
  };

  // Global listener to dismiss siren
  useEffect(() => {
    const handleGlobalClick = () => {
      if (isSirenActive) {
        if (stopSirenRef.current) stopSirenRef.current();
        setIsSirenActive(false);
        setSmsSent(false); // Dismiss banner
      }
    };

    if (isSirenActive) {
      // Delay attachment so the initial pointer up doesn't trigger dismissal instantly
      const timeout = setTimeout(() => {
        window.addEventListener('click', handleGlobalClick);
        window.addEventListener('touchstart', handleGlobalClick);
      }, 500);
      return () => {
        clearTimeout(timeout);
        window.removeEventListener('click', handleGlobalClick);
        window.removeEventListener('touchstart', handleGlobalClick);
      };
    }
  }, [isSirenActive]);

  // Bind the custom hook
  const sosPress = useLongPress(handleLongPress, callAmbulance, { delay: 5000 });

  return (
    <DataState loading={loading} error={error} loadingText="Verifying emergency protocols...">
      <div className="flex flex-col gap-6 h-full max-w-6xl mx-auto pt-4 relative">
        <PageHeader
          title={t('emergency.title')}
          subtitle={t('emergency.subtitle')}
          titleClassName="text-5xl lg:text-7xl"
          align="center"
          className="mb-12"
          badges={
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-red-100 text-red-600 border border-red-200 shadow-inner">
              <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
              <span className="text-xs font-bold uppercase tracking-wider">{t('emergency.urgent')}</span>
            </div>
          }
        />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* SOS Zone */}
        <div className="lg:col-span-12 xl:col-span-12 flex flex-col items-center justify-center bg-surface-container-lowest rounded-[2rem] p-12 mb-8 shadow-sm border border-red-100/50 relative overflow-hidden bg-glass border-ghost">
          {/* SMS Sent Banner */}
          {smsSent && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-red-600 text-white px-6 py-3 rounded-full flex items-center gap-3 shadow-xl z-20 animate-in slide-in-from-top fade-in duration-300">
              <Send className="w-5 h-5 animate-pulse" />
              <div className="flex flex-col">
                <span className="text-sm font-black tracking-widest uppercase">{t('global.smsDispatched')}</span>
                <span className="text-[10px] opacity-90">{t('global.locSent')}</span>
              </div>
            </div>
          )}

          <div className="relative z-10 flex flex-col items-center text-center w-full mt-4">
            <div className="mb-10 relative">
              <div className={`absolute inset-0 bg-red-500/20 blur-3xl rounded-full scale-150 ${sosPress.isPressing ? 'animate-ping' : 'animate-pulse'}`}></div>
              <button 
                {...sosPress}
                disabled={isLocating}
                className={`relative w-56 h-56 lg:w-80 lg:h-80 bg-gradient-to-br from-red-500 to-red-700 rounded-full flex flex-col items-center justify-center text-white border-[12px] border-white/80 shadow-[0_20px_60px_rgba(220,38,38,0.4)] transition-all duration-300 disabled:opacity-80 disabled:hover:scale-100 disabled:cursor-not-allowed ${sosPress.isPressing ? 'scale-90 border-red-100' : 'hover:scale-105 active:scale-95'}`}
              >
                {isLocating ? (
                  <Loader2 className="w-16 h-16 lg:w-20 lg:h-20 mb-2 animate-spin" />
                ) : (
                  <AlertOctagon className="w-16 h-16 lg:w-20 lg:h-20 mb-2" />
                )}
                
                <span className="text-4xl lg:text-5xl font-black tracking-tighter shadow-sm">{isLocating ? t('emergency.locating') : sosPress.isPressing ? sosPress.timeLeft : 'SOS'}</span>
                <span className="text-[10px] lg:text-xs font-bold uppercase tracking-[0.2em] mt-3 opacity-90 text-center px-4">
                  {isLocating ? t('emergency.findingHotline') : sosPress.isPressing ? t('emergency.alarmIn', { seconds: sosPress.timeLeft }) : t('emergency.sosHold')}
                </span>
              </button>
            </div>
            <div className="max-w-md mx-auto">
              {isLocating ? (
                <p className="font-bold text-red-600 mb-4 uppercase tracking-widest text-xs animate-pulse">{t('emergency.requestingCoordinates')}</p>
              ) : (
                <p className="font-bold text-red-600 mb-4 uppercase tracking-widest text-xs">{t('emergency.activating')}</p>
              )}
              <div className="flex flex-wrap justify-center gap-8 text-sm text-[var(--color-on-surface-variant)] font-bold">
                <span className="flex items-center gap-2"><Share2 className="w-4 h-4"/> {t('emergency.liveLoc')}</span>
                <span className="flex items-center gap-2 text-slate-400">
                  <Contact2 className="w-4 h-4"/> {t('emergency.callEmergencyContact')}
                </span>
              </div>
            </div>

            <div className="mt-8 w-full max-sm">
              <button 
                onClick={callAmbulance}
                disabled={isLocating}
                className="flex items-center justify-center gap-3 w-full px-6 py-4 bg-red-50 text-red-600 rounded-2xl hover:bg-red-100 transition-colors font-extrabold text-lg shadow-sm border border-red-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLocating ? <Loader2 className="w-6 h-6 animate-spin"/> : <PhoneCall className="w-6 h-6"/>}
                {t('emergency.ambulance')}: {emergencyNumber}
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-7 xl:col-span-8 space-y-8 h-full">
          {/* Quick Contacts */}
          <section>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold tracking-tight">{t('emergency.quickContacts')}</h2>
              <span className="text-xs font-bold text-[var(--color-on-surface-variant)] flex items-center gap-1">
                <LocateFixed className="w-4 h-4" /> {t('emergency.nearby')}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {locLoading ? (
                Array(2).fill(0).map((_, i) => (
                  <div key={i} className="p-6 bg-glass rounded-2xl border-ghost animate-pulse flex flex-col gap-4">
                    <div className="flex justify-between items-start">
                      <div className="w-12 h-12 bg-slate-200 rounded-xl"></div>
                      <div className="w-16 h-6 bg-slate-200 rounded-full"></div>
                    </div>
                    <div className="space-y-2">
                      <div className="h-6 bg-slate-200 rounded w-3/4"></div>
                      <div className="h-4 bg-slate-200 rounded w-1/2"></div>
                    </div>
                    <div className="mt-auto h-10 bg-slate-200 rounded-xl"></div>
                  </div>
                ))
              ) : displayFacilities.map((facility) => (
                <div key={facility.id} className="p-6 bg-glass rounded-2xl border-ghost shadow-[var(--shadow-liquid-hover)] hover:bg-white/80 transition-all flex flex-col">
                  <div className="flex justify-between items-start mb-4">
                    <div className={`p-3 rounded-xl ${facility.type === 'hospital' ? 'bg-blue-100 text-blue-600' : 'bg-red-100 text-red-600'}`}>
                      {facility.type === 'hospital' ? <ActivitySquare className="w-6 h-6" /> : <Ambulance className="w-6 h-6" />}
                    </div>
                    <span className={`text-xs font-bold px-3 py-1 rounded-full ${facility.type === 'hospital' ? 'bg-blue-50 text-blue-600' : 'bg-red-50 text-red-600'}`}>
                      {facility.distance}
                    </span>
                  </div>
                  <h3 className="font-bold text-lg mb-1">{facility.name}</h3>
                  <p className="text-sm text-[var(--color-on-surface-variant)] mb-2">{facility.details}</p>
                  {facility.arrivalMinutes && (
                    <p className="text-xs font-extrabold text-blue-600 uppercase tracking-widest mb-4 flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin"/> {t('emergency.estimatedArrival')}: {facility.arrivalMinutes} - {facility.arrivalMinutes + 4} {t('emergency.mins')}
                    </p>
                  )}
                  {!facility.arrivalMinutes && facility.type === 'ambulance' && (
                    <p className="text-sm text-[var(--color-on-surface-variant)] mb-4">{t('emergency.estimatedArrival')}: 8-12 {t('emergency.mins')}</p>
                  )}
                  {!facility.arrivalMinutes && facility.type !== 'ambulance' && (
                    <div className="mb-4 h-4"></div>
                  )}
                  <div className="flex gap-2 mt-auto">
                    <a 
                      href={facility.lat && facility.lng ? 
                        `https://www.google.com/maps/dir/?api=1&destination=${facility.lat},${facility.lng}` : 
                        `https://www.google.com/maps/search/${encodeURIComponent(facility.name + ' ' + (facility.details || ''))}`
                      }
                      target="_blank" rel="noopener noreferrer"
                      className="flex-1 bg-white border border-slate-200 py-3 flex items-center justify-center gap-2 rounded-xl text-xs font-bold hover:bg-slate-50 transition-colors text-slate-700"
                    >
                      <Navigation2 className="w-4 h-4" /> {t('emergency.directions')}
                    </a>
                    {facility.phone ? (
                      <a 
                        href={`tel:${facility.phone.replace(/[^0-9+]/g, '')}`}
                        className={`px-5 text-white rounded-xl flex items-center justify-center shadow-sm transition-colors hover:shadow-md ${facility.type === 'hospital' ? 'bg-[var(--color-primary)] hover:bg-blue-700' : 'bg-red-600 hover:bg-red-700'}`}
                      >
                        <Phone className="w-5 h-5" />
                      </a>
                    ) : (
                      <button 
                        disabled
                        className="px-5 text-slate-400 bg-slate-200 rounded-xl flex items-center justify-center cursor-not-allowed"
                        title="No phone number available"
                      >
                        <Phone className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Current Location Data */}
          <section className="bg-glass border-ghost rounded-3xl p-8 shadow-sm">
            <h2 className="text-xl font-bold mb-6">{t('emergency.currentLoc')}</h2>
            <div className="flex flex-col md:flex-row gap-8 items-center">
              <div className="w-full md:w-1/2 h-48 rounded-2xl overflow-hidden bg-slate-200 relative">
                {location ? (
                  <iframe 
                    width="100%" 
                    height="100%" 
                    frameBorder="0" 
                    scrolling="no" 
                    marginHeight="0" 
                    marginWidth="0" 
                    src={`https://www.openstreetmap.org/export/embed.html?bbox=${location.lng-0.002}%2C${location.lat-0.002}%2C${location.lng+0.002}%2C${location.lat+0.002}&layer=mapnik&marker=${location.lat}%2C${location.lng}`} 
                    className="w-full h-full object-cover">
                  </iframe>
                ) : (
                  <div className="w-full h-full bg-slate-100 flex items-center justify-center text-slate-400 font-bold uppercase tracking-widest text-xs">
                    {locLoading ? <Loader2 className="w-6 h-6 animate-spin" /> : t('emergency.mapUnavailable')}
                  </div>
                )}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  {/* Visual marker overlay if OSM marker takes too long to load */}
                  {!locLoading && location && (
                    <div className="w-10 h-10 bg-blue-600/20 rounded-full flex items-center justify-center border border-blue-600 animate-pulse">
                      <div className="w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-lg"></div>
                    </div>
                  )}
                </div>
              </div>
              <div className="w-full md:w-1/2 space-y-4">
                <div>
                  <p className="text-[10px] font-bold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-1">{t('global.preciseAddress')}</p>
                  <p className="text-lg font-bold leading-snug">{address || (locLoading ? t('global.processing') + '...' : t('emergency.addressUnavailable'))}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-[10px] font-bold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-1">{t('global.coordinates')}</p>
                    <p className="text-sm font-bold">
                      {location ? `${location.lat.toFixed(4)}° ${location.lat > 0 ? 'N' : 'S'}, ${Math.abs(location.lng).toFixed(4)}° ${location.lng > 0 ? 'E' : 'W'}` : (locLoading ? t('global.processing') + '...' : t('emergency.addressUnavailable'))}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-[var(--color-on-surface-variant)] uppercase tracking-widest mb-1">Signal Strength</p>
                    <p className="text-sm font-bold text-green-600 flex items-center gap-1">Excellent</p>
                  </div>
                </div>
                <button 
                  onClick={handleCopyLink}
                  disabled={!location}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-white/50 border border-white text-[var(--color-on-surface)] rounded-xl font-bold text-sm shadow-sm hover:bg-white/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Copy className="w-4 h-4" /> {t('emergency.copyShareLink')}
                </button>
              </div>
            </div>
          </section>
        </div>

        <div className="lg:col-span-5 xl:col-span-4 space-y-6">
          <div className="bg-slate-900 border border-slate-700 text-white rounded-3xl p-8 shadow-xl relative overflow-hidden group">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-xl font-bold flex items-center gap-2 text-white">
                <ActivitySquare className="w-5 h-5 text-blue-400" /> {t('emergency.essentialId')}
              </h3>
            </div>

            <div className="mb-6 pb-6 border-b border-white/10">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">{t('global.patientId')}</p>
              <h2 className="text-2xl font-black text-white tracking-tight leading-none mb-1">
                {userData.firstName || userData.lastName ? `${userData.firstName} ${userData.lastName}` : '-'}
              </h2>
              <p className="text-sm font-bold text-blue-400">ID: {userData.patientId || '-'}</p>
            </div>

            <div className="mb-6 pb-6 border-b border-white/10 flex flex-col gap-2">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">{t('medicalId.medicalInsurance')}</p>
              {(!userData.insurance?.cardImage || (userData.insurance?.providerName && userData.insurance.providerName !== '-' && userData.insurance.providerName !== '')) && (
                <div className="space-y-3">
                  <div>
                    <p className="text-[9px] font-bold uppercase tracking-widest opacity-40 mb-0.5">{t('global.primaryProvider')}</p>
                    <p className="text-sm font-black text-white">{userData.insurance?.providerName || '-'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-[9px] font-bold uppercase tracking-widest opacity-40 mb-0.5">{t('medicalId.memberId')}</p>
                      <p className="text-sm font-black text-blue-400">{userData.insurance?.memberId || '-'}</p>
                    </div>
                    <div className="text-end">
                      <p className="text-[9px] font-bold uppercase tracking-widest opacity-40 mb-0.5">{t('medicalId.groupNumber')}</p>
                      <p className="text-sm font-black text-white">{userData.insurance?.groupNumber || '-'}</p>
                    </div>
                  </div>
                </div>
              )}

              {userData.insurance?.cardImage && (
                <button 
                  onClick={() => setIsCardViewOpen(true)}
                  className="mt-4 w-full bg-blue-600/10 border border-blue-400/20 text-blue-400 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-blue-600 hover:text-white transition-all flex items-center justify-center gap-2 shadow-sm"
                >
                  <ActivitySquare className="w-4 h-4" />
                  {t('emergency.viewDigitalCardPhoto')}
                </button>
              )}
            </div>
            
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="border-b border-white/10 pb-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">{t('medicalId.bloodType')}</p>
                  <p className="text-2xl font-black text-red-400">{userData.bloodType || '-'}</p>
                </div>
                <div className="border-b border-white/10 pb-4 text-end">
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1 text-end">{t('emergency.weightHeight')}</p>
                  <p className="text-sm font-bold text-white">
                    {userData.weight ? `${userData.weight}${t('global.kg')}` : '-'} / {userData.height ? `${userData.height}${t('global.cm')}` : '-'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="border-b border-white/10 pb-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">{t('emergency.donorStatus')}</p>
                  <p className={`text-sm font-bold ${
                    userData.organDonor === 'Registered Donor' ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {userData.organDonor || t('medicalId.notRegistered')}
                  </p>
                </div>
                <div className="border-b border-white/10 pb-4 text-end">
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1 text-end">{t('medicalId.nationalId')}</p>
                  <p className="text-sm font-bold text-slate-300">{userData.nationalId || '-'}</p>
                </div>
              </div>

              <div className="border-b border-white/10 pb-4">
                <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">{t('medicalId.knownAllergies')}</p>
                <p className="text-sm font-bold">
                  {userData.allergies && userData.allergies.length > 0 
                    ? userData.allergies.map(a => a.name).join(', ') 
                    : '-'
                  }
                </p>
              </div>

              <div className="border-b border-white/10 pb-4">
                <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">{t('medicalId.chronicConditions')}</p>
                <p className="text-sm font-bold">{userData.chronicConditions && userData.chronicConditions.length > 0 ? userData.chronicConditions.map(c => c.name).join(', ') : '-'}</p>
              </div>

              <div className="border-b border-white/10 pb-4">
                <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">{t('medicalId.activeMeds')}</p>
                <p className="text-sm font-bold">
                  {userData.prescriptions && userData.prescriptions.length > 0 
                    ? userData.prescriptions.map(p => p.name).join(', ') 
                    : '-'
                  }
                </p>
              </div>

              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-2">{t('emergency.emergencyContactsTitle')}</p>
                <EmergencyContactsList variant="compact" allowEdit={false} />
              </div>
            </div>
            
            {/* Background elements */}
            <Droplet className="absolute -bottom-10 -right-10 w-48 h-48 text-white/5 opacity-10 rotate-12 pointer-events-none" />
          </div>

          <div className="bg-glass rounded-3xl p-8 border-ghost shadow-sm">
            <h3 className="font-bold mb-4">{t('emergency.firstAidTitle')}</h3>
            <div className="space-y-4">
              <div className="flex gap-4 p-3 rounded-xl bg-white/50">
                <div className="w-8 h-8 shrink-0 bg-white rounded-lg flex items-center justify-center font-black text-[var(--color-primary)] border border-slate-100">1</div>
                <p className="text-xs font-bold text-[var(--color-on-surface-variant)]">{t('emergency.step1')}</p>
              </div>
              <div className="flex gap-4 p-3 rounded-xl bg-white/50">
                <div className="w-8 h-8 shrink-0 bg-white rounded-lg flex items-center justify-center font-black text-[var(--color-primary)] border border-slate-100">2</div>
                <p className="text-xs font-bold text-[var(--color-on-surface-variant)]">{t('emergency.step2')}</p>
              </div>
              <div className="flex gap-4 p-3 rounded-xl bg-white/50">
                <div className="w-8 h-8 shrink-0 bg-white rounded-lg flex items-center justify-center font-black text-[var(--color-primary)] border border-slate-100">3</div>
                <p className="text-xs font-bold text-[var(--color-on-surface-variant)]">{t('emergency.step3')}</p>
              </div>
              <button 
                onClick={() => setIsFirstAidModalOpen(true)}
                className="w-full py-4 text-xs font-black text-blue-600 hover:bg-blue-50/50 rounded-2xl transition-all border border-transparent hover:border-blue-100 uppercase tracking-widest flex items-center justify-center gap-2"
              >
                <ActivitySquare className="w-4 h-4" />
                  {t('emergency.viewAllGuides')}
              </button>
            </div>
          </div>
        </div>
      </div>

      <FirstAidModal isOpen={isFirstAidModalOpen} onClose={() => setIsFirstAidModalOpen(false)} />
      <DigitalInsuranceCard isOpen={isCardViewOpen} onClose={() => setIsCardViewOpen(false)} />
      </div>
    </DataState>
  );
}
