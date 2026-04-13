import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from './ui/GlassCard';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Activity, X, ArrowRight, ArrowLeft, Heart, Check, Loader2 } from 'lucide-react';
import { UniversalImagePicker } from './ui/UniversalImagePicker';
import { useAuth } from '../context/AuthContext';
import { Select } from './ui/Select';
import { DatePicker } from './ui/DatePicker';
import apiClient from '../services/apiClient';

export function AuthModal({ isOpen, onClose }) {
  const { t, i18n } = useTranslation();
  const isRtl = i18n.dir() === 'rtl';
  const { updateUser, login } = useAuth();
  const [view, setView] = useState('login'); // 'login' or 'register'
  const [step, setStep] = useState(1);
  const [profileImage, setProfileImage] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  
  // Registration State
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    bloodType: 'Unknown',
    gender: 'M',
    dob: '',
    _hp_website: '' // Honeypot field
  });

  const [errors, setErrors] = useState({});
  
  // Reset modal state when it's opened
  React.useEffect(() => {
    if (isOpen) {
      switchView('login');
    }
  }, [isOpen]);

  const switchView = (v) => {
    setView(v);
    setStep(1);
    setProfileImage(null);
    setApiError('');
    setFormData({
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      bloodType: 'O+',
      gender: 'M',
      dob: '',
      _hp_website: ''
    });
  };

  const validateStep1 = () => {
    const newErrors = {};
    if (!formData.firstName.trim()) newErrors.firstName = t('auth.firstNameRequired');
    if (!formData.lastName.trim()) newErrors.lastName = t('auth.lastNameRequired');
    if (!profileImage) newErrors.profileImage = t('auth.profileImageRequired', { defaultValue: 'Profile image is required' });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors = {};
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim()) {
      newErrors.email = t('auth.emailRequired');
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = t('auth.invalidEmail');
    }

    // Password complexity: 8+ chars, 1 uppercase, 1 number, 1 symbol
    const password = formData.password;
    if (!password) {
      newErrors.password = t('auth.passwordRequired');
    } else {
      if (password.length < 8) newErrors.password = t('auth.passwordMin');
      else if (!/[A-Z]/.test(password)) newErrors.password = t('auth.passwordUpper');
      else if (!/[0-9]/.test(password)) newErrors.password = t('auth.passwordNumber');
      else if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) newErrors.password = t('auth.passwordSpecial');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    // Honeypot check - silently prevent progression without alerting bot
    if (formData._hp_website) return;
    
    if (step === 1 && !validateStep1()) return;
    if (step === 2 && !validateStep2()) return;
    setStep(prev => prev + 1);
    setErrors({});
    setApiError('');
  };
  const prevStep = () => {
    setStep(prev => prev - 1);
    setErrors({});
    setApiError('');
  };

  const handleComplete = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setApiError('');

    try {
      const response = await apiClient.post('/auth/register', {
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        password: formData.password,
        profileImage: profileImage,
        bloodType: formData.bloodType,
        gender: formData.gender,
        dateOfBirth: formData.dob || null,
      });

      const token = response.data.Token || response.data.token;
      const user = response.data.User || response.data.user || response.data.userProfile || {};

      await login(token, {
        ...user,
        firstName: user.FirstName || user.firstName || formData.firstName,
        lastName: user.LastName || user.lastName || formData.lastName,
        email: user.Email || user.email || formData.email,
        profileImage: profileImage, // Show local base64 immediately for speed
      });
      onClose();
    } catch (error) {
      const errMsg = error.response?.data?.title 
        || error.response?.data?.message 
        || 'Registration failed. Please try again.';
      setApiError(errMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogin = async () => {
    if (isSubmitting) return;
    
    const newErrors = {};
    if (formData._hp_website) return; // Honeypot trap
    
    if (!formData.email) newErrors.loginEmail = t('auth.emailRequired');
    if (!formData.password) newErrors.loginPassword = t('auth.passwordRequired');
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsSubmitting(true);
    setApiError('');

    try {
      const response = await apiClient.post('/auth/login', {
        email: formData.email,
        password: formData.password,
      });

      const token = response.data.Token || response.data.token;
      const user = response.data.User || response.data.user || response.data.userProfile || {};

      await login(token, {
        firstName: user.FirstName || user.firstName,
        lastName: user.LastName || user.lastName,
        email: user.Email || user.email,
        profileImage: user.ProfileImage || user.profileImage,
        patientId: user.PatientId || user.patientId,
        bloodType: user.BloodType || user.bloodType,
        gender: user.Gender || user.gender,
      });
      onClose();
    } catch (error) {
      const errMsg = error.response?.data?.title 
        || 'Invalid email or password.';
      setApiError(errMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <React.Fragment>
          {/* Backdrop Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[150]"
          />
          {/* Modal Content */}
          <div className="fixed inset-0 z-[150] flex items-center justify-center p-4" onClick={onClose}>
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 30 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg"
            >
              <GlassCard className="p-8 md:p-10 flex flex-col min-h-[500px] bg-glass-heavy border-ghost shadow-[0_40px_80px_rgba(0,91,192,0.2)] pb-12 max-h-[90vh] overflow-y-auto custom-scrollbar">
                <button 
                  onClick={onClose}
                  className={`absolute top-6 ${isRtl ? 'left-6' : 'right-6'} p-2 rounded-full hover:bg-white/40 transition-colors text-[var(--color-on-surface-variant)] z-50`}
                >
                  <X className="w-6 h-6" />
                </button>

                <div className="flex items-center gap-3 mb-8">
                  <div className="bg-primary-gradient p-2 rounded-2xl shadow-liquid-glass">
                    <Activity className="w-6 h-6 text-white" />
                  </div>
                  <h1 className="text-xl font-manrope font-bold text-[var(--color-primary)]">MedAgent</h1>
                </div>

                {/* API Error Banner */}
                {apiError && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-medium text-center"
                  >
                    {apiError}
                  </motion.div>
                )}

                <div className="flex-1 relative">
                  <AnimatePresence mode="wait">
                    {/* LOGIN VIEW */}
                    {view === 'login' && (
                      <motion.div
                        key="login"
                        initial={{ opacity: 0, x: -30 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 30 }}
                        transition={{ duration: 0.3 }}
                        className="flex flex-col gap-6"
                      >
                        <div>
                          <h2 className="text-2xl font-manrope font-bold text-[var(--color-on-surface)]">{t('auth.welcomeBack')}</h2>
                          <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">{t('auth.authDescription')}</p>
                        </div>
                        <Input 
                          id="email" 
                          type="email" 
                          label={t('auth.emailLabel')} 
                          placeholder={t('auth.emailPlaceholder')} 
                          value={formData.email}
                          onChange={(e) => setFormData(prev => ({...prev, email: e.target.value}))}
                          error={errors.loginEmail}
                        />
                        <Input 
                          id="password" 
                          type="password" 
                          label={t('auth.passwordLabel')} 
                          placeholder={t('auth.passwordPlaceholder')} 
                          value={formData.password}
                          onChange={(e) => setFormData(prev => ({...prev, password: e.target.value}))}
                          error={errors.loginPassword}
                        />
                        <Button 
                          variant="primary" 
                          className="w-full mt-2" 
                          onClick={handleLogin}
                          disabled={isSubmitting}
                        >
                          {isSubmitting ? (
                            <><Loader2 className="w-4 h-4 animate-spin me-2" /> {t('auth.authenticating', { defaultValue: 'Authenticating...' })}</>
                          ) : (
                            t('auth.authenticate')
                          )}
                        </Button>
                        <p className="text-center text-sm text-[var(--color-on-surface-variant)] mt-4">
                          {t('auth.noAccount')}{' '}
                          <button onClick={() => switchView('register')} className="text-[var(--color-primary)] font-semibold hover:underline">
                            {t('auth.registerSecurely')}
                          </button>
                        </p>
                      </motion.div>
                    )}

                    {/* REGISTER VIEW - STEP 1 */}
                    {view === 'register' && step === 1 && (
                      <motion.div
                        key="reg1"
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -30 }}
                        transition={{ duration: 0.3 }}
                        className="flex flex-col gap-6"
                      >
                        <div className="flex justify-between items-end">
                          <div>
                            <h2 className="text-2xl font-manrope font-bold text-[var(--color-on-surface)]">{t('auth.createAccount')}</h2>
                            <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">{t('auth.personalDetails')}</p>
                          </div>
                          <span className="text-sm font-medium text-[var(--color-on-surface-variant)]">1 / 3</span>
                        </div>
                        
                        {/* Profile Photo Slot */}
                        <div className="flex flex-col items-center gap-2 py-2">
                          <UniversalImagePicker 
                            onImageSelect={setProfileImage}
                            currentImage={profileImage}
                            shape="circle"
                            label={t('auth.profileAvatar')}
                            showAvatars={true}
                          />
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{t('auth.profileAvatar')}</span>
                          {errors.profileImage && <span className="text-xs text-red-500 font-bold mt-1 text-center">{errors.profileImage}</span>}
                        </div>

                        <Input 
                          id="firstName" 
                          label={t('auth.firstNameLabel')} 
                          placeholder={t('auth.firstNamePlaceholder')} 
                          value={formData.firstName}
                          onChange={(e) => setFormData(prev => ({...prev, firstName: e.target.value}))}
                          required
                          error={errors.firstName}
                        />
                        <Input 
                          id="lastName" 
                          label={t('auth.lastNameLabel')} 
                          placeholder={t('auth.lastNamePlaceholder')} 
                          value={formData.lastName}
                          onChange={(e) => setFormData(prev => ({...prev, lastName: e.target.value}))}
                          required
                          error={errors.lastName}
                        />
                        <Button variant="primary" onClick={nextStep} className="w-full mt-2">
                          {t('auth.continue')} <ArrowRight className="w-4 h-4 ms-2 rtl:-scale-x-100" />
                        </Button>
                        <p className="text-center text-sm text-[var(--color-on-surface-variant)] mt-4">
                          {t('auth.alreadyRegistered')}{' '}
                          <button onClick={() => switchView('login')} className="text-[var(--color-primary)] font-semibold hover:underline">
                            {t('auth.returnToLogin')}
                          </button>
                        </p>
                      </motion.div>
                    )}

                    {/* REGISTER VIEW - STEP 2 */}
                    {view === 'register' && step === 2 && (
                      <motion.div
                        key="reg2"
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -30 }}
                        transition={{ duration: 0.3 }}
                        className="flex flex-col gap-6"
                      >
                         <div className="flex justify-between items-end">
                          <div>
                            <h2 className="text-2xl font-manrope font-bold text-[var(--color-on-surface)]">{t('auth.accountAccess')}</h2>
                            <p className="text-sm text-[var(--color-on-surface-variant)] mt-1">{t('auth.secureCredentials')}</p>
                          </div>
                          <span className="text-sm font-medium text-[var(--color-on-surface-variant)]">2 / 3</span>
                        </div>
                        <Input 
                          id="email" 
                          type="email" 
                          label={t('auth.professionalEmail')} 
                          placeholder={t('auth.emailPlaceholder')} 
                          value={formData.email}
                          onChange={(e) => setFormData(prev => ({...prev, email: e.target.value}))}
                          required
                          error={errors.email}
                        />
                        <Input 
                          id="password" 
                          type="password" 
                          label={t('auth.passwordLabel')} 
                          placeholder={t('auth.passwordPlaceholder')} 
                          value={formData.password}
                          onChange={(e) => setFormData(prev => ({...prev, password: e.target.value}))}
                          required
                          error={errors.password}
                        />
                        <div className="absolute left-[-9999px] top-[-9999px]" aria-hidden="true">
                          <label htmlFor="_hp_website">Website</label>
                          <input 
                            type="text" 
                            id="_hp_website" 
                            name="_hp_website" 
                            tabIndex="-1" 
                            autoComplete="off"
                            value={formData._hp_website}
                            onChange={(e) => setFormData(prev => ({...prev, _hp_website: e.target.value}))}
                          />
                        </div>
                        <div className="flex gap-4 mt-2">
                          <Button variant="secondary" onClick={prevStep} className="flex-1 py-3"><ArrowLeft className="w-4 h-4 me-2 rtl:-scale-x-100" /> {t('auth.back')}</Button>
                          <Button variant="primary" onClick={nextStep} className="flex-1 py-3 group">
                            {t('auth.nextStep')} <ArrowRight className="w-4 h-4 ms-2 rtl:-scale-x-100 group-hover:translate-x-1 rtl:group-hover:-translate-x-1 transition-transform" />
                          </Button>
                        </div>
                      </motion.div>
                    )}

                    {/* REGISTER VIEW - STEP 3 (Optional Health Data) */}
                    {view === 'register' && step === 3 && (
                      <motion.div
                        key="reg3"
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -30 }}
                        transition={{ duration: 0.3 }}
                        className="flex flex-col gap-6"
                      >
                         <div className="flex justify-between items-end">
                          <div>
                            <h2 className="text-2xl font-manrope font-bold text-[var(--color-on-surface)]">{t('auth.healthProfile')}</h2>
                          </div>
                          <span className="text-sm font-medium text-[var(--color-on-surface-variant)]">3 / 3</span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <Select 
                            label={t('medicalId.bloodType')}
                            value={formData.bloodType}
                            onChange={(e) => setFormData(prev => ({ ...prev, bloodType: e.target.value }))}
                            options={[t('global.unknown'), "O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]}
                          />
                          <Select 
                            label={t('auth.biologicalGender')}
                            value={formData.gender}
                            onChange={(e) => setFormData({...formData, gender: e.target.value})}
                            options={[
                              { label: t('global.female'), value: 'F' },
                              { label: t('global.male'), value: 'M' }
                            ]}
                          />
                        </div>

                        <DatePicker 
                          label={t('auth.dob')} 
                          value={formData.dob}
                          onChange={(e) => setFormData({...formData, dob: e.target.value})}
                          placeholder={t('auth.dateOfBirthPlaceholder')}
                        />

                        <div className="flex gap-4 mt-2">
                          <Button variant="secondary" onClick={prevStep} className="flex-1 py-3">{t('auth.back')}</Button>
                          <Button 
                            variant="primary" 
                            onClick={handleComplete} 
                            disabled={isSubmitting}
                            className="flex-1 py-3 bg-green-600 hover:bg-green-700 flex items-center justify-center gap-2"
                          >
                            {isSubmitting ? (
                              <><Loader2 className="w-5 h-5 animate-spin" /> {t('auth.registering', { defaultValue: 'Creating...' })}</>
                            ) : (
                              <><Check className="w-5 h-5" /> {t('auth.complete')}</>
                            )}
                          </Button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        </React.Fragment>
      )}
    </AnimatePresence>
  );
}
