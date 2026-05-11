import React, { useState } from 'react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { CheckCircle2, PhoneCall, Droplet, Activity, Ruler, Shield, Heart, FileText, Lock, Plus, Camera, Pill } from 'lucide-react';

import femaleAvatar from '../assets/female-avatar.svg';
import maleAvatar from '../assets/male-avatar.svg';
import { useTranslation } from 'react-i18next';
import { EmergencyContactsList } from '../components/contact/EmergencyContactsList';
import { AddContactModal } from '../components/contact/AddContactModal';
import { ProfileActions } from '../components/medical-id/ProfileActions';
import { useAuth } from '../context/AuthContext';
import { UpdateHealthModal } from '../components/medical/UpdateHealthModal';
import { InsuranceModal } from '../components/medical/InsuranceModal';
import { DigitalInsuranceCard } from '../components/medical/DigitalInsuranceCard';
import { SensitiveField } from '../components/ui/SensitiveField';
import { Pencil } from 'lucide-react';

export default function MedicalID() {
  const { t, i18n } = useTranslation();
  const isRtl = i18n ? i18n.dir() === 'rtl' : false;
  const { userData, updateUser } = useAuth();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [isInsuranceModalOpen, setIsInsuranceModalOpen] = useState(false);
  const [isCardViewOpen, setIsCardViewOpen] = useState(false);

  // Handle local image update for immediate feedback, and sync to context
  const handleProfileImageChange = (newImage) => {
    updateUser({ profileImage: newImage });
  };

  const displayImage = userData.profileImage || (userData.gender === 'F' ? femaleAvatar : maleAvatar);

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pt-6 h-full pb-20">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Profile Column */}
        <div className="lg:col-span-4 space-y-8 h-full flex flex-col">
          {/* Patient Profile Card */}
          <div className="bg-glass border-ghost rounded-[2rem] p-8 shadow-[0_20px_40px_rgba(25,28,30,0.04)] relative overflow-hidden group">
            {userData.isRegistered && (
              <div className="absolute top-0 right-0 p-6 z-10">
                <span className="bg-blue-100 text-blue-600 text-[10px] font-black px-3 py-1 rounded-full tracking-widest uppercase shadow-sm border border-blue-200/50">{t('medicalId.premiumMember')}</span>
              </div>
            )}
            <div className="flex flex-col items-center text-center space-y-6 relative z-10 mt-2">
              <div className="relative">
                <div className="w-32 h-32 rounded-full p-1 bg-gradient-to-tr from-blue-600 to-indigo-400 shadow-xl">
                  <img alt={`${userData.firstName} ${userData.lastName}`} className="w-full h-full rounded-full object-cover border-4 border-white isolate" src={displayImage} />
                </div>
                <div className="absolute bottom-1 right-1 bg-white p-1.5 rounded-full shadow-sm border border-slate-100">
                  <CheckCircle2 className="w-6 h-6 text-blue-600 fill-blue-600/20" />
                </div>
              </div>
              <div className="space-y-1">
                <h1 className="text-3xl font-extrabold tracking-tight text-[#191c1e]">
                  {userData.firstName || userData.lastName 
                    ? `${userData.firstName} ${userData.lastName}` 
                    : '-'
                  }
                </h1>
                <p className="text-slate-500 font-bold tracking-wide">{t('medicalId.patientIdLabel')}: <SensitiveField className="text-blue-600" value={userData.patientId} /></p>
              </div>
              <ProfileActions 
                onUpdateHealth={() => setIsUpdateModalOpen(true)}
                onImageSelect={handleProfileImageChange}
                className="mt-2"
              />
            </div>
            
            {/* Background elements */}
            <div className="absolute top-0 right-0 -mt-20 -mr-20 w-64 h-64 bg-blue-100 blur-3xl opacity-50 rounded-full pointer-events-none"></div>
          </div>

          {/* Emergency Contact */}
          <div className="bg-slate-50/80 backdrop-blur-sm rounded-[2.5rem] p-8 space-y-6 border border-slate-200/60 shadow-inner flex-1">
            <h3 className="text-xl font-extrabold text-[#191c1e] flex items-center justify-between w-full">
              <span className="flex items-center gap-2">
                <span className="text-red-500">
                  <Heart className="w-6 h-6 fill-red-500" />
                </span>
                {t('medicalId.emergencyContact')}
              </span>
              <button 
                onClick={() => setIsAddModalOpen(true)}
                className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center hover:bg-blue-600 hover:text-white transition-colors shadow-sm"
              >
                <Plus className="w-5 h-5" />
              </button>
            </h3>
            <EmergencyContactsList variant="detailed" allowDelete={true} />
          </div>
        </div>

        {/* Dashboard Content Column */}
        <div className="lg:col-span-8 space-y-8">
          {/* Vital Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bg-glass border-ghost p-6 rounded-[2rem] shadow-sm hover:translate-y-[-4px] transition-transform">
              <Droplet className="w-8 h-8 text-red-500 mb-4 fill-red-100" />
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{t('medicalId.bloodType')}</p>
              <p className="text-2xl font-black text-[#191c1e] tracking-tighter w-full">{userData.bloodType || '-'}</p>
            </div>
            <div className="bg-glass border-ghost p-6 rounded-[2rem] shadow-sm hover:translate-y-[-4px] transition-transform">
              <Activity className="w-8 h-8 text-blue-600 mb-4" />
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{t('medicalId.weight')}</p>
              <p className="text-2xl font-black text-[#191c1e] tracking-tighter">
                {userData.weight ? (
                  <>{userData.weight} <span className="text-base font-bold text-slate-500 tracking-normal">{t('global.kg')}</span></>
                ) : '-'}
              </p>
            </div>
            <div className="bg-glass border-ghost p-6 rounded-[2rem] shadow-sm hover:translate-y-[-4px] transition-transform">
              <Ruler className="w-8 h-8 text-blue-600 mb-4 fill-blue-100" />
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{t('medicalId.height')}</p>
              <p className="text-2xl font-black text-[#191c1e] tracking-tighter">
                {userData.height ? (
                  <>{userData.height} <span className="text-base font-bold text-slate-500 tracking-normal">{t('global.cm')}</span></>
                ) : '-'}
              </p>
            </div>
            <div className="bg-glass border-ghost p-6 rounded-[2rem] shadow-sm hover:translate-y-[-4px] transition-transform">
              <Shield className="w-8 h-8 text-orange-500 mb-4" />
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{t('medicalId.nationalId')}</p>
              <p className="text-2xl font-black text-[#191c1e] tracking-tighter"><SensitiveField value={userData.nationalId} fallback="-" /></p>
            </div>
          </div>

          {/* Medical Insurance Card */}
          <div className="bg-glass border-ghost rounded-[2.5rem] p-10 shadow-[var(--shadow-liquid-hover)] relative overflow-hidden group">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center">
                  <Shield className="w-8 h-8 text-blue-600 fill-blue-600/20" />
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-extrabold tracking-tight text-[#191c1e]">{t('medicalId.medicalInsurance')}</h2>
                    <button 
                      onClick={() => setIsInsuranceModalOpen(true)}
                      className="p-1.5 rounded-full hover:bg-blue-50 text-blue-400 hover:text-blue-600 transition-all border border-transparent hover:border-blue-100"
                      title={t('medicalId.editInsurance')}
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-slate-500 font-bold mt-0.5 flex items-center gap-2">
                    {!userData.insurance?.providerName && !userData.insurance?.cardImage ? (
                      <span className="text-slate-400">{t('medicalId.noInsurance')}</span>
                    ) : userData.insurance?.cardImage ? (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                        <span className="text-emerald-500 font-extrabold uppercase tracking-wide text-xs">{t('medicalId.verifiedPhoto')}</span>
                      </>
                    ) : (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                        <span className="text-blue-600 font-extrabold uppercase tracking-wide text-xs">{t('medicalId.manualData')}</span>
                      </>
                    )}
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setIsCardViewOpen(true)}
                disabled={!userData.insurance?.providerName && !userData.insurance?.cardImage}
                className="flex items-center gap-3 bg-[#191c1e] text-white px-7 py-3.5 rounded-2xl font-bold hover:shadow-lg hover:shadow-black/20 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <span className="flex items-center gap-2">
                  <Camera className="w-4 h-4 opacity-60 group-hover:opacity-100 transition-opacity" />
                  {t('medicalId.viewDigitalCard')}
                </span>
                <span className="opacity-60 text-lg group-hover:translate-x-1 rtl:group-hover:-translate-x-1 transition-transform ms-1">{isRtl ? '←' : '→'}</span>
              </button>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 mt-10 pt-10 border-t border-slate-200/60 relative z-10">
              <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{t('medicalId.providerName')}</p>
                <p className="text-lg font-extrabold text-[#191c1e] tracking-tight">{userData.insurance?.providerName || '-'}</p>
              </div>
              <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{t('medicalId.memberId')}</p>
                <p className="text-lg font-extrabold text-[#191c1e] tracking-tight">{userData.insurance?.memberId || '-'}</p>
              </div>
              <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{t('medicalId.groupNumber')}</p>
                <p className="text-lg font-extrabold text-[#191c1e] tracking-tight">{userData.insurance?.groupNumber || '-'}</p>
              </div>
              <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{t('medicalId.planType')}</p>
                <p className="text-lg font-extrabold text-[#191c1e] tracking-tight">{userData.insurance?.planType || '-'}</p>
              </div>
            </div>

            {/* Decorative background logo */}
            <Shield className="absolute -bottom-10 -right-10 w-48 h-48 text-blue-500/5 rotate-12 pointer-events-none" />
          </div>

          {/* Allergies & Conditions */}
          <div className="bg-glass border-ghost rounded-[2.5rem] p-10 space-y-10 shadow-[var(--shadow-liquid)]">
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-extrabold tracking-tight text-[#191c1e]">{t('medicalId.knownAllergies')}</h2>
                  <button 
                    onClick={() => setIsUpdateModalOpen(true)}
                    className="p-1.5 rounded-full hover:bg-blue-50 text-blue-400 hover:text-blue-600 transition-all border border-transparent hover:border-blue-100"
                    title={t('medicalId.editAllergies')}
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                </div>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] bg-slate-100 px-3 py-1 rounded-md border border-slate-200">
                  {t('medicalId.lastVerified')}: {userData.lastVerified}
                </span>
              </div>
              
              <div className="flex flex-wrap gap-4">
                {userData.allergies && userData.allergies.length > 0 ? userData.allergies.map((allergy, index) => (
                  <div key={allergy.id || index} className={`flex items-center gap-3 border px-6 py-4 rounded-2xl shadow-sm ${
                    allergy.severity === 'Severe' ? 'bg-red-50 border-red-100' : 
                    allergy.severity === 'Moderate' ? 'bg-orange-50 border-orange-100' : 'bg-slate-100 border-slate-200'
                  }`}>
                    <div className={`w-3 h-3 rounded-full ${
                      allergy.severity === 'Severe' ? 'bg-red-500 animate-pulse border border-red-600' : 
                      allergy.severity === 'Moderate' ? 'bg-orange-500 border border-orange-600' : 'bg-slate-400 border border-slate-500'
                    }`}></div>
                    <span className={`font-extrabold tracking-tight text-lg ${
                      allergy.severity === 'Severe' ? 'text-red-900' : 
                      allergy.severity === 'Moderate' ? 'text-orange-900' : 'text-slate-700'
                    }`}>{allergy.name || '-'}</span>
                    <span className={`text-[10px] px-2.5 py-1 rounded-lg uppercase font-black tracking-widest text-white ${
                      allergy.severity === 'Severe' ? 'bg-red-500' : 
                      allergy.severity === 'Moderate' ? 'bg-orange-500' : 'bg-slate-400'
                    }`}>
                      {allergy.severity || 'Mild'}
                    </span>
                  </div>
                )) : (
                  <p className="text-4xl font-black text-slate-300 tracking-tighter">-</p>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-extrabold tracking-tight text-[#191c1e]">{t('medicalId.chronicConditions')}</h2>
                <button 
                  onClick={() => setIsUpdateModalOpen(true)}
                  className="p-1.5 rounded-full hover:bg-blue-50 text-blue-400 hover:text-blue-600 transition-all border border-transparent hover:border-blue-100"
                  title={t('medicalId.editConditions')}
                >
                  <Pencil className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {userData.chronicConditions && userData.chronicConditions.length > 0 ? userData.chronicConditions.map((condition) => (
                  <div key={condition.id} className="p-6 bg-slate-50/80 rounded-[2rem] border border-slate-200/60 shadow-inner">
                    <h4 className="font-extrabold text-lg text-[#191c1e] mb-2 tracking-tight">{condition.name || '-'}</h4>
                    <p className="text-slate-500 font-medium text-sm leading-relaxed">
                      {condition.description || t('medicalId.defaultConditionDesc')}
                    </p>
                  </div>
                )) : (
                  <p className="text-4xl font-black text-slate-300 tracking-tighter">-</p>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-extrabold tracking-tight text-[#191c1e]">{t('medicalId.activeMeds')}</h2>
                  <a 
                    href="/medicines"
                    onClick={(e) => { e.preventDefault(); window.location.href='/medicines'; }}
                    className="p-1.5 rounded-full hover:bg-blue-50 text-blue-400 hover:text-blue-600 transition-all border border-transparent hover:border-blue-100"
                    title={t('medicalId.manageMeds')}
                  >
                    <Pencil className="w-4 h-4" />
                  </a>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {userData.prescriptions && userData.prescriptions.length > 0 ? userData.prescriptions.map((px) => (
                  <div key={px.id} className="p-6 bg-white border border-slate-100 rounded-[2rem] shadow-sm hover:shadow-md transition-all group flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-500 shrink-0 border border-blue-100/50 group-hover:bg-blue-600 group-hover:text-white transition-all">
                      <Pill className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-extrabold text-lg text-[#191c1e] mb-1 tracking-tight">{px.name}</h4>
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-relaxed">
                        {px.freq} {px.time ? `• ${px.time.split('•')[0].trim()}` : ''}
                      </p>
                    </div>
                  </div>
                )) : (
                  <p className="text-4xl font-black text-slate-300 tracking-tighter">-</p>
                )}
              </div>
            </div>

            <div className="pt-10 border-t border-slate-200/60">
              <div className="flex flex-col md:flex-row gap-8 items-start text-start">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <h4 className="font-extrabold text-[#191c1e] tracking-tight text-lg">{t('medicalId.organDonor')}</h4>
                    <button 
                      onClick={() => setIsUpdateModalOpen(true)}
                      className="p-1.5 rounded-full hover:bg-blue-50 text-blue-400 hover:text-blue-600 transition-all border border-transparent hover:border-blue-100"
                      title={t('medicalId.editOrganDonor')}
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                  </div>
                  <div className={`flex items-center gap-2 font-bold ${
                    userData.organDonor === 'Registered Donor' ? 'text-emerald-600' : 'text-red-500'
                  }`}>
                    <Heart className={`w-5 h-5 ${
                      userData.organDonor === 'Registered Donor' ? 'fill-emerald-500' : 'fill-red-500'
                    }`} />
                    {userData.organDonor || t('medicalId.notRegistered')}
                  </div>
                </div>
                <div className="flex-1 space-y-2">
                  <h4 className="font-extrabold text-[#191c1e] tracking-tight text-lg">{t('medicalId.advanceDirectives')}</h4>
                  <div className="flex items-center gap-2 text-slate-500 font-bold">
                    <FileText className="w-5 h-5 text-slate-400" />
                    {userData.advanceDirectives || t('medicalId.notRegistered')}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-blue-50/50 rounded-[2rem] p-8 border border-blue-100 flex items-start gap-6 shadow-sm group">
            <div className="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center shrink-0 shadow-lg shadow-blue-600/20">
              <Lock className="w-6 h-6 text-white" />
            </div>
            <div className="space-y-2 flex-1">
              <h4 className="text-xl font-extrabold text-blue-600 tracking-tight">{t('medicalId.emergencyAccess')}</h4>
              <p className="text-sm text-slate-600 font-medium leading-relaxed max-w-2xl text-start">
                {t('medicalId.emergencyAccessDesc', { level: userData.emergencyAccessibility })}
              </p>
            </div>
          </div>
        </div>
      </div>

      <AddContactModal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} />
      <UpdateHealthModal isOpen={isUpdateModalOpen} onClose={() => setIsUpdateModalOpen(false)} />
      <InsuranceModal isOpen={isInsuranceModalOpen} onClose={() => setIsInsuranceModalOpen(false)} />
      <DigitalInsuranceCard isOpen={isCardViewOpen} onClose={() => setIsCardViewOpen(false)} />
    </div>
  );
}
