import React, { useState, useEffect, useRef } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Menu, X, User, Globe } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from './ui/Button';
import { AuthModal } from './AuthModal';
import { useAuth } from '../context/AuthContext';
import { LogOut, ChevronDown } from 'lucide-react';

export function TopNavLayout() {
  const { t, i18n } = useTranslation();
  const { isAuthenticated, userData, logout } = useAuth();
  const navigate = useNavigate();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const location = useLocation();
  const langMenuRef = useRef(null);
  const userMenuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (langMenuRef.current && !langMenuRef.current.contains(event.target)) {
        setIsLangMenuOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isRtl = i18n.dir() === 'rtl';

  const navLinks = [
    { name: t('nav.home'), path: '/' },
    { name: t('nav.contact'), path: '/contact' },
    ...(isAuthenticated ? [{ name: t('nav.medicines'), path: '/medicines' }] : []),
    { name: t('nav.scan'), path: '/scans' },
    ...(isAuthenticated && userData.isRegistered ? [{ name: t('nav.medicalId'), path: '/id' }] : []),
    { name: t('nav.emergency'), path: '/emergency' },
  ];

  return (
    <div className="min-h-screen w-full flex flex-col relative overflow-hidden">
      {/* Dynamic Native 3D Floating Orbs for the entire app */}
      <motion.div
        animate={{ y: [-20, 20, -20], scale: [1, 1.05, 1], rotate: [0, 5, 0] }}
        transition={{ repeat: Infinity, duration: 15, ease: "easeInOut" }}
        className="fixed top-[-10%] left-[-10%] w-[40vw] h-[40vw] rounded-full bg-blue-300/30 blur-[130px] pointer-events-none z-0"
      />
      <motion.div
        animate={{ y: [0, -30, 0], scale: [1, 1.1, 1], rotate: [0, -5, 0] }}
        transition={{ repeat: Infinity, duration: 12, ease: "easeInOut", delay: 2 }}
        className="fixed bottom-[10%] right-[-5%] w-[35vw] h-[35vw] rounded-full bg-cyan-300/20 blur-[120px] pointer-events-none z-0"
      />

      {/* Top Navigation Bar */}
      <header className="fixed top-0 inset-x-0 h-20 bg-white/40 border-b border-ghost backdrop-blur-2xl z-40 lg:px-10 px-6 flex items-center justify-between shadow-[0_4px_30px_rgba(0,91,192,0.03)] selection:bg-none">
        
        <div className="flex items-center gap-4">
          <button 
            className="xl:hidden p-2 rounded-xl bg-white/50 border border-ghost text-[var(--color-primary)] mr-2 transition-transform active:scale-95"
            onClick={() => setMobileMenuOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="bg-primary-gradient p-2.5 rounded-2xl shadow-liquid-glass">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-manrope font-bold text-[var(--color-primary)] tracking-tight">MedAgent</span>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden xl:flex items-center gap-1 bg-white/50 p-1.5 rounded-full border border-ghost shadow-inner">
          {navLinks.map(link => {
            const isEmergency = link.path === '/emergency';
            return (
              <NavLink
                key={link.name}
                to={link.path}
                className={({ isActive }) => 
                  `relative px-5 py-2.5 rounded-full text-sm font-medium font-inter transition-all duration-300 ${
                    isActive 
                      ? isEmergency 
                        ? 'bg-red-600 text-white shadow-sm' 
                        : 'text-[var(--color-primary)] shadow-sm' 
                      : isEmergency
                        ? 'text-red-500 hover:text-white hover:bg-red-500'
                        : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-white/40'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && !isEmergency && (
                      <motion.div
                        layoutId="nav-pill"
                        className="absolute inset-0 bg-white rounded-full shadow-[0_2px_10px_rgba(0,91,192,0.06)]"
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10">{link.name}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Auth / Profile  */}
        <div className="flex items-center gap-1 bg-white/50 p-1.5 rounded-full border border-ghost shadow-inner">
          <div className="relative" ref={langMenuRef}>
            <button 
              onClick={() => setIsLangMenuOpen(!isLangMenuOpen)} 
              className={`flex items-center justify-center px-4 py-2.5 rounded-full text-sm font-medium font-inter transition-all duration-300 ${isLangMenuOpen ? 'bg-red-500/80 text-white shadow-sm' : 'text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-white hover:shadow-[0_8px_20px_rgba(0,91,192,0.15)] hover:-translate-y-[1px] hover:scale-[1.02]'}`}
              title={t('nav.language')}
            >
              <Globe className="w-5 h-5 mx-auto" />
            </button>
            <AnimatePresence>
              {isLangMenuOpen && (
                <motion.div 
                  initial={{ opacity: 0, y: 15, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                  className={`absolute top-full mt-3 w-36 bg-slate-800/80 backdrop-blur-3xl p-3 rounded-[1.5rem] shadow-2xl border border-slate-700/50 flex flex-col gap-2 z-50 ${isRtl ? 'left-0' : 'right-0'}`}
                >
                  <button 
                    onClick={() => { i18n.changeLanguage('en'); setIsLangMenuOpen(false); }}
                    className={`flex items-center justify-between px-3 py-2.5 rounded-2xl backdrop-blur-xl shadow-sm border text-xs font-bold transition-all ${i18n.language === 'en' ? 'bg-[var(--color-primary)] border-[var(--color-primary)] text-white' : 'bg-white/90 border-white text-[#191c1e] hover:bg-[var(--color-primary)]/80 hover:text-white hover:border-transparent'}`}
                  >
                    English
                    {i18n.language === 'en' && <span className="w-2 h-2 rounded-full bg-white ml-2"></span>}
                  </button>
                  <button 
                    onClick={() => { i18n.changeLanguage('ar'); setIsLangMenuOpen(false); }}
                    className={`flex items-center justify-between px-3 py-2.5 rounded-2xl backdrop-blur-xl shadow-sm border text-xs font-bold transition-all ${i18n.language === 'ar' ? 'bg-[var(--color-primary)] border-[var(--color-primary)] text-white' : 'bg-white/90 border-white text-[#191c1e] hover:bg-[var(--color-primary)]/80 hover:text-white hover:border-transparent'}`}
                  >
                    العربية
                    {i18n.language === 'ar' && <span className="w-2 h-2 rounded-full bg-white mr-2"></span>}
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          {userData.isRegistered ? (
            <div className="relative" ref={userMenuRef}>
              <button 
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full hover:bg-white hover:shadow-sm transition-all border border-transparent hover:border-ghost"
              >
                <div className="w-8 h-8 rounded-full bg-primary-gradient flex items-center justify-center text-white text-[10px] font-black border border-white shadow-sm overflow-hidden">
                  {userData.profileImage ? (
                    <img src={userData.profileImage} alt="User" className="w-full h-full object-cover" />
                  ) : (
                    <User className="w-4 h-4" />
                  )}
                </div>
                <span className="text-xs font-bold text-[#191c1e] hidden sm:block">
                  {userData.firstName ? t('nav.hiUser', { name: userData.firstName }) : t('nav.medicalProfile')}
                </span>
                <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isUserMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {isUserMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className={`absolute top-full mt-3 w-48 bg-white rounded-3xl shadow-2xl border border-ghost p-2 z-50 overflow-hidden ${isRtl ? 'left-0' : 'right-0'}`}
                  >
                    <NavLink
                      to="/id"
                      onClick={() => setIsUserMenuOpen(false)}
                      className="flex items-center gap-3 w-full p-4 rounded-t-2xl hover:bg-slate-50 text-xs font-bold text-slate-700 transition-all"
                    >
                      <User className="w-4 h-4 text-blue-500" />
                      {t('nav.medicalProfile')}
                    </NavLink>
                    <button 
                      onClick={() => { 
                        logout(); 
                        setIsUserMenuOpen(false);
                        navigate('/');
                      }}
                      className="flex items-center gap-3 w-full p-4 rounded-b-2xl hover:bg-red-50 text-xs font-bold text-red-500 transition-all"
                    >
                      <LogOut className="w-4 h-4" />
                      {t('nav.logout')}
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <button 
              onClick={() => setIsAuthOpen(true)} 
              className="flex items-center px-4 py-2.5 rounded-full text-sm font-medium font-inter transition-all duration-300 text-[var(--color-on-surface-variant)] hover:text-[var(--color-on-surface)] hover:bg-white hover:shadow-[0_8px_20px_rgba(0,91,192,0.15)] hover:-translate-y-[1px] hover:scale-[1.02]"
            >
              <User className="w-4 h-4 mr-2 hidden sm:block" />
              <span className="hidden sm:inline">{t('nav.signIn')}</span>
              <span className="sm:hidden text-xs">{t('nav.login')}</span>
            </button>
          )}
        </div>
      </header>

      {/* Mobile Nav Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
              className="fixed inset-0 bg-[#001355]/20 backdrop-blur-sm z-40 xl:hidden"
            />
            {/* Left/Right Side Drawer */}
            <motion.div 
              initial={{ x: isRtl ? "100%" : "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: isRtl ? "100%" : "-100%" }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className={`fixed inset-y-0 ${isRtl ? 'right-0 border-l' : 'left-0 border-r'} w-72 bg-glass-heavy backdrop-blur-3xl z-50 flex flex-col p-6 xl:hidden border-ghost shadow-[20px_0_40px_rgba(0,91,192,0.15)] overflow-y-auto`}
            >
              <div className="flex justify-between items-center mb-8">
                <div className="flex items-center gap-3">
                  <div className="bg-primary-gradient p-2 rounded-xl shadow-sm">
                    <Activity className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-lg font-manrope font-bold text-[var(--color-primary)]">MedAgent</span>
                </div>
                <button 
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 rounded-full bg-white/50 border border-ghost text-slate-500 hover:text-red-500 active:scale-95 transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <nav className="flex flex-col gap-3 flex-1">
                {navLinks.map(link => {
                  const isEmergency = link.path === '/emergency';
                  return (
                    <NavLink
                      key={link.name}
                      to={link.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={({ isActive }) => 
                        `p-4 rounded-[1.5rem] flex items-center text-lg font-bold font-inter transition-all ${
                          isActive 
                            ? isEmergency ? 'bg-red-600 text-white shadow-liquid-glass' : 'bg-primary-gradient text-white shadow-liquid-glass' 
                            : isEmergency ? 'bg-white/50 text-red-500 border border-red-200 hover:bg-red-500 hover:text-white' : 'bg-white/50 text-[var(--color-on-surface-variant)] border border-ghost hover:bg-white'
                        }`
                      }
                    >
                      {link.name}
                    </NavLink>
                  );
                })}
              </nav>
              
              <div className="mt-8">
                {userData.isRegistered ? (
                  <div className="flex flex-col gap-3">
                    <NavLink
                      to="/id"
                      onClick={() => setMobileMenuOpen(false)}
                      className="w-full p-4 rounded-[1.5rem] bg-white/50 border border-ghost text-lg font-bold text-slate-700 flex items-center gap-3"
                    >
                      <User className="w-5 h-5 text-blue-500" />
                      {t('nav.medicalProfile')}
                    </NavLink>
                    <button 
                      onClick={() => { 
                        logout(); 
                        setMobileMenuOpen(false); 
                        navigate('/');
                      }}
                      className="w-full p-4 rounded-[1.5rem] bg-red-50 text-red-500 border border-red-100 text-lg font-bold flex items-center justify-center gap-3"
                    >
                      <LogOut className="w-5 h-5" />
                      {t('nav.logout')}
                    </button>
                  </div>
                ) : (
                  <Button variant="primary" onClick={() => { setIsAuthOpen(true); setMobileMenuOpen(false); }} className="w-full p-4 text-base shadow-liquid-glass">
                    <User className="w-5 h-5 mr-3" />
                    {t('nav.signInRegister')}
                  </Button>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main Content Area (Outlet renders the child routes) */}
      <main className="flex-1 pt-[100px] px-4 md:px-8 pb-8 z-10 w-full max-w-[2560px] mx-auto min-h-[calc(100vh-100px)] relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="h-full"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Global Footer - Hidden on Chat Dashboard to prevent double footers and scroll */}
      {location.pathname !== '/' && (
        <footer className="w-full py-6 px-6 border-t border-ghost bg-white/20 backdrop-blur-xl z-20 overflow-hidden relative">
          <div className="max-w-7xl mx-auto flex flex-col items-center gap-4 text-center">
            <div className="flex flex-col items-center gap-2 max-w-3xl">
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 bg-amber-50 text-amber-600 rounded-full text-[9px] font-black uppercase tracking-widest border border-amber-100">
                {t('chat.disclaimerTitle')}
              </div>
              <p className="text-[10px] font-bold text-slate-500 leading-tight italic opacity-70">
                {t('chat.disclaimerInfo')} <span className="text-red-600">{t('chat.emergencyCall')}</span> {t('chat.button')} <span className="text-red-600">{t('global.realDoctor')}</span>
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="bg-primary-gradient p-1 rounded-lg">
                  <Activity className="w-3 h-3 text-white" />
                </div>
                <span className="text-xs font-manrope font-black text-[var(--color-primary)]">MedAgent</span>
              </div>
              <div className="h-4 w-px bg-slate-200/50" />
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em]">
                {t('nav.copyright')}
              </p>
            </div>
          </div>
        </footer>
      )}

      {/* Login / Registration Modal */}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </div>
  );
}
