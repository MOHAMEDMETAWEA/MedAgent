import React, { useState } from 'react';
import { Phone, PhoneCall, Loader2, User, Trash2, Pencil } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useEmergency } from '../../context/EmergencyContext';
import { AddContactModal } from './AddContactModal';
import maleAvatar from '../../assets/male-avatar.svg';

export function EmergencyContactsList({ variant = 'compact', allowDelete = false, allowEdit = true }) {
  const { t } = useTranslation();
  const { contacts, removeContact } = useEmergency();
  const [contactToDelete, setContactToDelete] = useState(null);
  
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingContact, setEditingContact] = useState(null);

  const handleEdit = (contact) => {
    setEditingContact(contact);
    setIsEditModalOpen(true);
  };

  const confirmDelete = () => {
    if (contactToDelete) {
      removeContact(contactToDelete.id);
      setContactToDelete(null);
    }
  };

  if (!contacts || contacts.length === 0) {
    return (
      <div className="bg-slate-50 border border-slate-200 border-dashed rounded-3xl p-6 flex items-center justify-center text-center">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">{t('emergency.noContacts', 'No emergency contacts added yet.')}</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4 w-full">
        {contacts.map((contact, index) => (
          <div key={contact.id || index}>
            {variant === 'detailed' ? (
              <div className="bg-white p-5 rounded-3xl flex items-center justify-between shadow-sm border border-slate-100 group">
                <div className="flex items-center gap-4">
                  {contact.avatar ? (
                    <img 
                      src={contact.avatar} 
                      alt={contact.name} 
                      onError={(e) => { e.target.src = maleAvatar; }}
                      className="w-12 h-12 rounded-full object-cover border-2 border-slate-100" 
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                      <User className="w-5 h-5" />
                    </div>
                  )}
                  <div>
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{contact.relation}</p>
                    <p className="text-lg font-extrabold text-[#191c1e] tracking-tight">{contact.name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {allowEdit && (
                    <button
                      onClick={() => handleEdit(contact)}
                      className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 hover:bg-blue-600 hover:text-white transition-colors shadow-sm"
                      title="Edit"
                    >
                      <Pencil className="w-5 h-5" />
                    </button>
                  )}
                  {allowDelete && (
                    <button
                      onClick={() => setContactToDelete(contact)}
                      className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center text-red-500 hover:bg-red-600 hover:text-white transition-colors shadow-sm"
                      title={t('common.delete', 'Delete')}
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}
                  <a href={`tel:${contact.phone.replace(/[^0-9+]/g, '')}`} className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 hover:bg-blue-600 hover:text-white transition-colors shadow-sm">
                    <PhoneCall className="w-5 h-5" />
                  </a>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between group">
                <div className="flex items-center gap-3">
                  {contact.avatar ? (
                    <img 
                      src={contact.avatar} 
                      alt={contact.name} 
                      onError={(e) => { e.target.src = maleAvatar; }}
                      className="w-10 h-10 rounded-full object-cover border border-slate-200" 
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-bold truncate">{contact.name}</p>
                    <p className="text-[10px] opacity-60">{contact.relation} • {contact.phone}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {allowEdit && (
                    <button 
                      onClick={() => handleEdit(contact)}
                      className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-blue-600 transition-colors"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <a href={`tel:${contact.phone.replace(/[^0-9+]/g, '')}`}>
                    <Phone className="w-4 h-4 text-blue-400 group-hover:text-white transition-colors cursor-pointer ms-1 shrink-0" />
                  </a>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Delete Confirmation Modal */}
      {contactToDelete && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 bg-[#0f172a]/40 backdrop-blur-md transition-opacity"
            onClick={() => setContactToDelete(null)}
          />
          <div className="relative bg-white/80 backdrop-blur-3xl border border-white/40 shadow-[var(--shadow-liquid)] w-full max-w-sm rounded-[2.5rem] overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-8 flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-red-50 border-2 border-red-100 flex items-center justify-center mb-2 shadow-inner">
                <Trash2 className="w-8 h-8 text-red-500" />
              </div>
              <h3 className="text-xl font-extrabold text-[#191c1e] tracking-tight">Delete Contact?</h3>
              <p className="text-slate-500 font-medium text-sm leading-relaxed">
                Are you sure you want to remove <span className="font-extrabold text-[#191c1e]">{contactToDelete.name}</span> from your emergency contacts? This action cannot be undone.
              </p>
              <div className="flex gap-3 w-full mt-4">
                <button 
                  onClick={() => setContactToDelete(null)}
                  className="flex-1 py-4 bg-white/60 border border-slate-200 backdrop-blur-sm text-slate-700 font-bold rounded-2xl hover:bg-white hover:shadow-sm transition-all"
                >
                  {t('emergency.cancel', 'Cancel')}
                </button>
                <button 
                  onClick={confirmDelete}
                  className="flex-1 py-4 bg-red-500 text-white font-bold rounded-2xl hover:bg-red-600 shadow-lg shadow-red-500/20 active:scale-[0.98] transition-all text-sm"
                >
                  {t('emergency.delete', 'Delete')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal Hook */}
      <AddContactModal 
        isOpen={isEditModalOpen}
        onClose={() => { setIsEditModalOpen(false); setEditingContact(null); }}
        contactToEdit={editingContact}
      />
    </>
  );
}
