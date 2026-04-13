import React, { useState, useEffect } from 'react';
import { X, Pill, Info, Plus, ChevronDown, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { TimePicker } from '../ui/TimePicker';

export function AddMedicineModal({ isOpen, onClose, onSave, pxToEdit = null }) {
  const { t } = useTranslation();
  const [isAnySelectOpen, setIsAnySelectOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    dosage: '',
    desc: '',
    supply: '',
    type: 'Chronic Care',
    freq: 'Daily',
    time: 'Morning • 08:00 AM'
  });

  const [isCustom, setIsCustom] = useState(false);
  const [customTime, setCustomTime] = useState('08:00 AM');

  useEffect(() => {
    if (pxToEdit) {
      setFormData(pxToEdit);
      const isPredefined = [
        t('medicines.timeMorning', 'Morning • 08:00 AM'),
        t('medicines.timeNoon', 'Noon • 01:00 PM'),
        t('medicines.timeEvening', 'Evening • 06:00 PM'),
        t('medicines.timeNightly', 'Nightly • 09:00 PM')
      ].includes(pxToEdit.time);
      
      if (!isPredefined) {
        setIsCustom(true);
        setCustomTime(pxToEdit.time);
      } else {
        setIsCustom(false);
      }
    } else {
      setFormData({
        name: '',
        dosage: '',
        desc: '',
        supply: '',
        type: t('medicines.typeChronic', 'Chronic Care'),
        freq: t('medicines.freqDaily', 'Daily'),
        time: t('medicines.timeMorning', 'Morning • 08:00 AM')
      });
      setIsCustom(false);
    }
  }, [pxToEdit, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      ...formData,
      time: isCustom ? customTime : formData.time,
      id: pxToEdit?.id || Date.now(),
      status: pxToEdit?.status || 'impending',
      category: formData.time.includes('Morning') ? 'primary' : formData.time.includes('Noon') ? 'tertiary' : 'secondary'
    });
    onClose();
  };

  const modalShiftY = isAnySelectOpen ? -160 : 0;

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
            className="fixed inset-0 bg-[#0c0d0e]/60 backdrop-blur-md z-[99998]"
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
              className="w-full max-w-xl bg-white/95 backdrop-blur-3xl rounded-[2.5rem] border border-slate-200/60 shadow-[0_40px_80px_rgba(0,0,0,0.15)] flex flex-col max-h-[90vh] overflow-hidden"
            >
              <div className="flex items-center justify-between p-8 border-b border-slate-100 shrink-0">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-600/20">
                    <Pill className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-black text-slate-900 tracking-tight">
                      {pxToEdit ? t('medicines.editPrescription') : t('medicines.new')}
                    </h2>
                    <p className="text-[10px] font-black text-blue-600/60 uppercase tracking-widest mt-1">
                      {t('medicines.clinicalMode')}
                    </p>
                  </div>
                </div>
                <button 
                  onClick={onClose} 
                  className="p-3 bg-slate-50 hover:bg-slate-100 ms-auto rounded-2xl text-slate-400 hover:text-slate-900 transition-all border border-slate-100 active:scale-90"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                 <div className="grid grid-cols-2 gap-x-6 gap-y-8 mb-10">
                   <div className="col-span-2 md:col-span-1 space-y-2">
                     <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2.5 px-1 text-start">
                       {t('medicines.medicineName')}
                     </label>
                     <input 
                       type="text" 
                       required
                       className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200/60 rounded-2xl text-sm font-bold text-slate-900 placeholder:text-slate-300 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all outline-none"
                       placeholder={t('medicines.placeholderName')}
                       value={formData.name}
                       onChange={(e) => setFormData({...formData, name: e.target.value})}
                     />
                   </div>
                   <div className="col-span-2 md:col-span-1 space-y-2">
                     <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2.5 px-1 text-start">
                       {t('medicines.dosageStrength')}
                     </label>
                     <input 
                       type="text" 
                       required
                       className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200/60 rounded-2xl text-sm font-bold text-slate-900 placeholder:text-slate-300 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all outline-none"
                       placeholder={t('medicines.placeholderDosage')}
                       value={formData.dosage}
                       onChange={(e) => setFormData({...formData, dosage: e.target.value})}
                     />
                   </div>
                   
                   <div className="col-span-2 space-y-2">
                     <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2.5 px-1 text-start">
                       {t('medicines.clinicalDesc')}
                     </label>
                     <input 
                       type="text" 
                       className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200/60 rounded-2xl text-sm font-bold text-slate-900 placeholder:text-slate-300 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all outline-none"
                       placeholder={t('medicines.placeholderDesc')}
                       value={formData.desc}
                       onChange={(e) => setFormData({...formData, desc: e.target.value})}
                     />
                   </div>

                   <div className="col-span-2 md:col-span-1 space-y-2">
                     <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-2.5 px-1 text-start">
                       {t('medicines.currentSupply')}
                     </label>
                     <input 
                       type="number" 
                       required
                       className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200/60 rounded-2xl text-sm font-bold text-slate-900 placeholder:text-slate-300 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all outline-none"
                       placeholder={t('medicines.placeholderSupply')}
                       value={formData.supply}
                       onChange={(e) => setFormData({...formData, supply: e.target.value})}
                     />
                   </div>

                   <Select 
                     label={t('medicines.medicationType', 'Medication Type')}
                     value={formData.type}
                     onOpenChange={setIsAnySelectOpen}
                     shiftY={modalShiftY}
                     options={[
                       t('medicines.typeChronic', 'Chronic Care'),
                       t('medicines.typeMetabolic', 'Metabolic'),
                       t('medicines.typeStatins', 'Statins'),
                       t('medicines.typeVitamins', 'Vitamins'),
                       t('medicines.typeAntibiotics', 'Antibiotics')
                     ]}
                     onChange={(e) => setFormData({...formData, type: e.target.value})}
                   />

                    <Select 
                      label={t('medicines.frequency', 'Frequency')}
                      value={formData.freq}
                      onOpenChange={setIsAnySelectOpen}
                      shiftY={modalShiftY}
                      options={[
                        t('medicines.freqDaily', 'Daily'),
                        t('medicines.freq2x', '2x Day'),
                        t('medicines.freq3x', '3x Day'),
                        t('medicines.freqWeekly', 'Weekly'),
                        t('medicines.freqAsNeeded', 'As Needed')
                      ]}
                      onChange={(e) => setFormData({...formData, freq: e.target.value})}
                    />
                    <Select 
                      label={t('medicines.timeOfDay', 'Time of Day')}
                      onOpenChange={setIsAnySelectOpen}
                      shiftY={modalShiftY}
                      value={isCustom ? t('medicines.timeCustom', 'Custom Time...') : formData.time}
                      options={[
                        t('medicines.timeMorning', 'Morning • 08:00 AM'), 
                        t('medicines.timeNoon', 'Noon • 01:00 PM'), 
                        t('medicines.timeEvening', 'Evening • 06:00 PM'), 
                        t('medicines.timeNightly', 'Nightly • 09:00 PM'),
                        t('medicines.timeCustom', 'Custom Time...')
                      ]}
                      onChange={(e) => {
                        const val = e.target.value;
                        const morning = t('medicines.timeMorning', 'Morning • 08:00 AM');
                        const noon = t('medicines.timeNoon', 'Noon • 01:00 PM');
                        const custom = t('medicines.timeCustom', 'Custom Time...');
                        if (val === custom) {
                          setIsCustom(true);
                        } else {
                          setIsCustom(false);
                          setFormData({
                            ...formData, 
                            time: val, 
                            category: val === morning ? 'primary' : val === noon ? 'tertiary' : 'secondary'
                          });
                        }
                      }}
                    />
                    
                    {isCustom && (
                      <motion.div 
                        initial={{ opacity: 0, x: -10 }} 
                        animate={{ opacity: 1, x: 0 }}
                        className="col-span-2 md:col-span-1"
                      >
                        <TimePicker 
                          label={t('medicines.setPreciseTime', 'Set Precise Time')}
                          value={customTime}
                          onOpenChange={setIsAnySelectOpen}
                          shiftY={modalShiftY}
                          onChange={(e) => setCustomTime(e.target.value)}
                        />
                      </motion.div>
                    )}
                 </div>

                 <div className="p-5 bg-blue-50/50 rounded-2xl border border-blue-100 flex gap-4">
                   <Info className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                   <p className="text-xs font-bold text-blue-700 leading-relaxed text-start">
                     {t('medicines.medicationInfo', 'This medication will be added to your global clinical profile and scheduled in your daily timeline.')}
                   </p>
                 </div>
              </form>

              <div className="p-8 border-t border-slate-100 bg-slate-50/30 shrink-0 flex gap-3">
                <button 
                  type="button"
                  onClick={onClose}
                  className="px-8 py-4 text-xs font-black text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {t('medicines.cancel', 'Cancel')}
                </button>
                <button 
                  onClick={handleSubmit}
                  className="flex-1 bg-blue-600 text-white rounded-2xl py-4 text-xs font-black shadow-xl shadow-blue-600/20 active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  {pxToEdit ? t('medicines.updateRecord', 'Update Clinical Record') : t('medicines.saveRecord', 'Save Prescription')}
                </button>
              </div>
            </motion.div>
          </div>
        </React.Fragment>
      )}
    </AnimatePresence>
  );
}
