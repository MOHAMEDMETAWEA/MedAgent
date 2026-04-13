import React, { useState, useEffect } from 'react';
import { X, UserPlus, Pencil, Phone, User, Heart } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { UniversalImagePicker } from '../ui/UniversalImagePicker';
import { useEmergency } from '../../context/EmergencyContext';
import { Select } from '../ui/Select';
import apiClient from '../../services/apiClient';

export function AddContactModal({ isOpen, onClose, contactToEdit = null }) {
  const { t } = useTranslation();
  const { addContact, updateContact } = useEmergency();
  const [isSelectOpen, setIsSelectOpen] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    relation: t('emergency.relationships.Friend'),
    image: null
  });
  const [error, setError] = useState('');

  const relationships = [
    t('emergency.relationships.Mother'),
    t('emergency.relationships.Father'),
    t('emergency.relationships.Parent'),
    t('emergency.relationships.Brother'),
    t('emergency.relationships.Sister'),
    t('emergency.relationships.Child'), 
    t('emergency.relationships.Friend'),
    t('emergency.relationships.Spouse'),
    t('emergency.relationships.Partner'),
    t('emergency.relationships.Assistant'),
    t('emergency.relationships.Manager'),
    t('emergency.relationships.Primary Physician'),
    t('emergency.relationships.Specialist')
  ];
  
  useEffect(() => {
    if (contactToEdit) {
      setFormData({
        name: contactToEdit.name || '',
        phone: contactToEdit.phone || '',
        relation: contactToEdit.relation || t('emergency.relationships.Friend'),
        image: contactToEdit.avatar || null
      });
    } else {
      setFormData({ name: '', phone: '', relation: t('emergency.relationships.Friend'), image: null });
    }
    setError('');
  }, [contactToEdit, isOpen, t]);

  const handleImageSelect = (base64) => {
    setFormData({ ...formData, image: base64 });
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!formData.image) {
      setError(t('auth.profileImageRequired', { defaultValue: 'Image is required' }));
      return;
    }
    if (!formData.name || !formData.phone) return;
    setError('');

    let photoUrl = formData.image;

    // Upload to backend if it's a new image (base64)
    if (formData.image.startsWith('data:image')) {
      try {
        const uploadData = new FormData();
        const base64Response = await fetch(formData.image);
        const blob = await base64Response.blob();
        uploadData.append('file', blob, 'contact.jpg');
        uploadData.append('category', 'Contact');

        const response = await apiClient.post('/photos', uploadData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        photoUrl = `/api/photos/content/${response.data.id}`;
      } catch (err) {
        console.error("Failed to upload contact photo", err);
      }
    }

    const contactData = {
      name: formData.name,
      phone: formData.phone,
      relation: formData.relation,
      translatedRelationKey: formData.relation,
      avatar: photoUrl,
      type: [t('emergency.relationships.Primary Physician'), t('emergency.relationships.Specialist')].includes(formData.relation) ? 'medical' : 'family'
    };

    if (contactToEdit) {
      updateContact(contactToEdit.id, contactData);
    } else {
      addContact({
        id: Date.now(),
        ...contactData
      });
    }

    onClose();
  };

  const modalShiftY = isSelectOpen ? -120 : 0;

  return (
    <AnimatePresence>
      {isOpen && (
        <React.Fragment>
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-[#0f172a]/40 backdrop-blur-md z-[99998]"
          />
          
          {/* Modal Container */}
          <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4" onClick={onClose}>
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 40 }}
              animate={{ 
                opacity: 1, 
                scale: 1, 
                y: modalShiftY 
              }}
              exit={{ opacity: 0, scale: 0.9, y: 40 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="relative bg-white/95 backdrop-blur-3xl border border-slate-200/60 shadow-2xl w-full max-w-md rounded-[2.5rem] overflow-hidden flex flex-col"
            >
              <div className="flex items-center justify-between p-7 border-b border-slate-200/50">
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
                    {contactToEdit ? <Pencil className="w-5 h-5" /> : <UserPlus className="w-5 h-5" />}
                  </div>
                  <h2 className="text-xl font-black text-[#191c1e] tracking-tight">
                    {contactToEdit ? t('emergency.editContact') : t('emergency.addContact')}
                  </h2>
                </div>
                <button 
                  onClick={onClose} 
                  className="p-3 bg-slate-100 hover:bg-slate-200 ms-auto rounded-2xl transition-all active:scale-95 text-slate-500"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-8 space-y-8 overflow-y-auto max-h-[70vh] custom-scrollbar">
                {/* Avatar Upload */}
                <div className="flex flex-col items-center justify-center gap-4 pt-2">
                  <UniversalImagePicker 
                    onImageSelect={handleImageSelect}
                    currentImage={formData.image}
                    shape="circle"
                    label={contactToEdit ? t('emergency.updatePhoto') : t('emergency.addPhoto')}
                    showAvatars={true}
                  />
                  <div className="flex flex-col items-center text-center">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t('emergency.avatarDesc')}</span>
                    <p className="text-[10px] font-bold text-slate-400/60 mt-1">{contactToEdit ? t('emergency.changePhoto') : t('emergency.uploadPhoto')}</p>
                    {error && <span className="text-[10px] text-red-500 font-bold mt-1 bg-red-50 px-2 py-0.5 rounded-full">{error}</span>}
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2.5 px-1 text-start">
                      {t('emergency.fullName')}
                    </label>
                    <div className="relative group">
                      <User className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                      <input 
                        type="text" 
                        required
                        minLength={2}
                        value={formData.name}
                        onChange={e => setFormData({...formData, name: e.target.value})}
                        placeholder={t('emergency.namePlaceholder', 'e.g. Eleanor Fitzwilliam')}
                        className="w-full bg-slate-50/50 border border-slate-200/60 p-4 pl-12 rounded-2xl outline-none focus:bg-white focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 transition-all font-bold text-[#191c1e] placeholder:text-slate-200"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2.5 px-1 text-start">
                      {t('emergency.phone')}
                    </label>
                    <div className="relative group">
                      <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                      <input 
                        type="tel" 
                        required
                        pattern="[0-9]+"
                        value={formData.phone}
                        onChange={e => setFormData({...formData, phone: e.target.value.replace(/\D/g, '')})}
                        placeholder={t('emergency.phonePlaceholder', 'e.g. 01000000000')}
                        className="w-full bg-slate-50/50 border border-slate-200/60 p-4 pl-12 rounded-2xl outline-none focus:bg-white focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 transition-all font-bold text-[#191c1e] placeholder:text-slate-200"
                      />
                    </div>
                  </div>

                  <Select 
                    label={t('emergency.relationship')}
                    value={formData.relation}
                    options={relationships}
                    onOpenChange={setIsSelectOpen}
                    shiftY={modalShiftY}
                    onChange={(e) => setFormData({...formData, relation: e.target.value})}
                  />
                </div>
              </div>

              <div className="p-8 border-t border-slate-100 bg-slate-50/30 flex gap-3">
                <button 
                  type="button"
                  onClick={onClose}
                  className="px-6 py-4 text-xs font-black text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {t('emergency.cancel', 'Cancel')}
                </button>
                <button 
                  onClick={handleSubmit}
                  className="flex-1 bg-blue-600 text-white font-black text-xs tracking-widest uppercase p-4 rounded-2xl hover:bg-blue-700 hover:shadow-xl hover:shadow-blue-600/20 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                >
                  {contactToEdit ? <Pencil className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
                  {contactToEdit ? t('emergency.editContact') : t('emergency.addContact')}
                </button>
              </div>
            </motion.div>
          </div>
        </React.Fragment>
      )}
    </AnimatePresence>
  );
}
