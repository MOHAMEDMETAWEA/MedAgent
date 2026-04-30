import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Download, Plus, MapPin, Search, ThermometerSun, Divide as SunDim, Moon, AlertTriangle, Pill, Activity, MoreHorizontal, Bolt, Calendar, LayoutGrid, Pencil, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '../components/ui/PageHeader';
import { DataState } from '../components/ui/DataState';
import { useAuth } from '../context/AuthContext';
import { AddMedicineModal } from '../components/medical/AddMedicineModal';
import { usePrescriptions } from '../hooks/usePrescriptions';

export default function Medicines() {
  const { t } = useTranslation();
  const { userData, updateUser } = useAuth();
  const {
    prescriptions,
    activePrescriptions,
    archivedPrescriptions,
    handleToggleStatus,
    handleAddMedicine: addMedicinesHook,
    handleDelete,
    handleToggleArchive,
    lowSupplyPx
  } = usePrescriptions();

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState('today');
  const [isRefillDismissed, setIsRefillDismissed] = useState(false);
  const [editingPx, setEditingPx] = useState(null);
  const [showArchived, setShowArchived] = useState(false);

  const handleEdit = (px) => {
    setEditingPx(px);
    setIsAddModalOpen(true);
  };

  const handleAddMedicine = (newPx) => {
    addMedicinesHook(newPx, editingPx?.id);
    setEditingPx(null);
    setIsAddModalOpen(false);
  };

  const handleExportCSV = () => {
    if (prescriptions.length === 0) return;
    
    const headers = [
      t('medicines.csvHeaders.name'), 
      t('medicines.csvHeaders.dosage'), 
      t('medicines.csvHeaders.type'), 
      t('medicines.csvHeaders.frequency'), 
      t('medicines.csvHeaders.nextDose'), 
      t('medicines.csvHeaders.supply'), 
      t('medicines.csvHeaders.status')
    ];
    const rows = prescriptions.map(px => [
      px.name,
      px.dosage || '-',
      px.type,
      px.freq,
      px.time,
      px.supply || '30',
      px.status
    ]);

    const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `MedAgent_Prescriptions_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const completedCount = prescriptions.filter(px => px.status === 'completed').length;
  const adherenceRate = prescriptions.length > 0 
    ? Math.round((completedCount / prescriptions.length) * 100) 
    : 0;

  return (
    <div className="flex flex-col gap-6 h-full max-w-6xl mx-auto pt-6">
      <PageHeader 
        title={t('medicines.title')} 
        subtitle={t('medicines.subtitle')}
      >
        <button 
          onClick={handleExportCSV}
          className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-white border border-slate-200/60 px-5 py-2.5 rounded-full text-sm font-semibold text-on-surface hover:bg-slate-50 transition-all shadow-sm active:scale-95"
        >
          <Download className="w-5 h-5 text-slate-500" />
          {t('medicines.export')}
        </button>
        <button 
          onClick={() => setIsAddModalOpen(true)}
          className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-[var(--color-primary)] text-white px-6 py-2.5 rounded-full text-sm font-semibold hover:shadow-lg transition-all shadow-[var(--color-primary)]/20 active:scale-95"
        >
          <Plus className="w-5 h-5" />
          {t('medicines.new')}
        </button>
      </PageHeader>

      <div className="grid grid-cols-12 gap-8 items-start">
        {/* Daily Timeline */}
        <section className="col-span-12 lg:col-span-8 space-y-8">
          <div className="card-premium">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-xl font-extrabold text-[#191c1e]">
                {viewMode === 'today' ? t('medicines.dailyIntake') : t('medicines.weeklyMedications')}
              </h2>
              <div className="flex bg-slate-100 p-1 rounded-full border border-slate-200/50">
                <button 
                  onClick={() => setViewMode('today')}
                  className={`px-5 py-1.5 rounded-full text-xs font-bold transition-all ${
                    viewMode === 'today' ? 'bg-white shadow-sm text-slate-900 font-extrabold' : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {t('medicines.today')}
                </button>
                <button 
                  onClick={() => setViewMode('week')}
                  className={`px-5 py-1.5 rounded-full text-xs font-bold transition-all ${
                    viewMode === 'week' ? 'bg-white shadow-sm text-slate-900 font-extrabold' : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {t('medicines.week')}
                </button>
              </div>
            </div>

            {activePrescriptions.length === 0 ? (
              <div className="py-20 border-2 border-dashed border-slate-200 rounded-[2.5rem] flex flex-col items-center justify-center text-center gap-4 bg-slate-50/30">
                <div className="w-16 h-16 rounded-3xl bg-white flex items-center justify-center text-slate-300 shadow-sm border border-slate-100">
                  <Calendar className="w-8 h-8" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-400">{t('global.noMedications')}</h3>
                  <p className="text-xs font-bold text-slate-400/60 uppercase tracking-widest mt-1">{t('global.addFirstScript')}</p>
                </div>
                <button 
                  onClick={() => setIsAddModalOpen(true)}
                  className="mt-2 text-xs font-black text-blue-600 bg-blue-50 px-6 py-2.5 rounded-full border border-blue-100 hover:bg-blue-600 hover:text-white transition-all shadow-sm active:scale-95"
                >
                  {t('medicines.setSchedule')}
                </button>
              </div>
            ) : (
              <div className="space-y-6 relative before:absolute before:left-[1.35rem] before:top-2 before:bottom-2 before:w-[2px] before:bg-slate-100">
                {viewMode === 'week' && (
                  <div className="bg-slate-100/50 p-4 rounded-2xl mb-8 border border-slate-200/50">
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest text-center">
                      {t('medicines.weeklyOverview')}
                    </p>
                  </div>
                )}
                {activePrescriptions.map((px, idx) => (
                   <div key={idx} className="relative pl-12 group">
                     {/* Time Indicator */}
                     <div className={`absolute left-0 top-1 w-11 h-11 rounded-full flex items-center justify-center z-10 border-4 border-white ${
                       px.time.includes('Morning') ? 'bg-blue-100 text-blue-600' : 
                       px.time.includes('Noon') ? 'bg-orange-100 text-orange-600' : 'bg-slate-800 text-slate-200'
                     }`}>
                       {px.time.includes('Morning') ? <ThermometerSun className="w-5 h-5" /> : 
                        px.time.includes('Noon') ? <SunDim className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                     </div>
                     <div className="flex-1">
                       <p className={`text-xs font-black mb-1 uppercase tracking-widest ${
                          px.time.includes('Morning') ? 'text-blue-600' : 
                          px.time.includes('Noon') ? 'text-orange-600' : 'text-slate-600'
                       }`}>{px.time}</p>
                       <div className="flex items-center gap-4 bg-white/60 p-4 rounded-2xl group-hover:bg-white transition-all shadow-sm border border-ghost">
                         <div className={`w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-sm border border-slate-100 ${
                           px.time.includes('Morning') ? 'text-blue-600' : 
                           px.time.includes('Noon') ? 'text-orange-600' : 'text-slate-600'
                         }`}>
                           <Pill className="w-6 h-6" />
                         </div>
                          <div>
                            <h4 className="font-extrabold text-[#191c1e] text-lg leading-tight">
                              {px.name} {px.dosage && <span className="text-slate-400 font-bold ml-1">{px.dosage}</span>}
                            </h4>
                            <p className="text-sm font-semibold text-[#434656] mt-0.5">
                              {viewMode === 'today' ? (
                                px.time.includes('Morning') ? t('medicines.takeMorning') : 
                                px.time.includes('Noon') ? t('medicines.takeNoon') : 
                                t('medicines.takeNight')
                              ) : (
                                `${t('medicines.scheduled')}: ${px.freq}`
                              )}
                            </p>
                          </div>
                         <div className="ml-auto flex items-center gap-2">
                           <button 
                             onClick={() => handleEdit(px)}
                             className="w-10 h-10 rounded-2xl flex items-center justify-center bg-slate-50 text-slate-400 hover:bg-blue-50 hover:text-blue-600 border border-slate-100 transition-all"
                             title={t('medicines.editPrescription')}
                           >
                             <Pencil className="w-4 h-4" />
                           </button>
                           <button 
                             onClick={() => handleDelete(px.id)}
                             className="w-10 h-10 rounded-2xl flex items-center justify-center bg-slate-50 text-slate-400 hover:bg-red-50 hover:text-red-600 border border-slate-100 transition-all"
                             title={t('medicines.deleteRecord')}
                           >
                             <Trash2 className="w-4 h-4" />
                           </button>
                           <div className="w-px h-6 bg-slate-100 mx-1" />
                           <button 
                             onClick={() => handleToggleStatus(px.id)}
                             className={`w-10 h-10 rounded-2xl flex items-center justify-center transition-all shadow-sm overflow-hidden relative group/btn ${
                               px.status === 'completed' 
                               ? 'bg-blue-600 text-white shadow-blue-500/30' 
                               : 'bg-slate-50 text-slate-400 hover:bg-blue-50 hover:text-blue-600 border border-slate-100'
                             }`}
                           >
                             <Check className={`w-5 h-5 transition-transform duration-300 ${px.status === 'completed' ? 'scale-110 stroke-[3px]' : 'scale-90 opacity-40 group-hover/btn:scale-110 group-hover/btn:opacity-100'}`} />
                           </button>
                         </div>
                       </div>
                     </div>
                   </div>
                ))}
              </div>
            )}
          </div>

          {/* Refill Alerts */}
          {lowSupplyPx && !isRefillDismissed && (
            <motion.div 
              initial={{ height: 0, opacity: 0, scale: 0.95 }}
              animate={{ height: 'auto', opacity: 1, scale: 1 }}
              exit={{ height: 0, opacity: 0, scale: 0.95 }}
              className="bg-blue-600 p-8 rounded-[2rem] text-white overflow-hidden relative shadow-lg shadow-blue-600/20 mb-8"
            >
              <div className="absolute -right-20 -top-20 w-64 h-64 bg-white/20 rounded-full blur-3xl pointer-events-none"></div>
              <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="flex items-start gap-6">
                  <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center text-white shrink-0 border border-white/30">
                    <AlertTriangle className="w-8 h-8" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black mb-2 tracking-tight">{t('global.refillAlert')}</h3>
                    <p className="text-blue-50/90 max-w-md font-medium leading-relaxed">
                      {t('medicines.lowSupplyAlert', { 
                        name: lowSupplyPx.name, 
                        supply: lowSupplyPx.supply, 
                        unit: lowSupplyPx.unit || 'units' 
                      })} 
                      {parseInt(lowSupplyPx.supply || '0') <= 3 
                        ? ` ${t('medicines.urgentRefill')}` 
                        : ` ${t('medicines.considerRefill')}`}
                    </p>
                  </div>
                </div>
                <div className="flex gap-4 shrink-0 flex-col sm:flex-row w-full sm:w-auto">
                  {lowSupplyPx.status === 'refill_requested' ? (
                    <div className="flex items-center gap-3 bg-white/20 backdrop-blur-md px-8 py-3 rounded-full border border-white/30 text-white font-bold">
                      <Check className="w-5 h-5 text-blue-100" />
                      {t('medicines.refillAuthorized')}
                    </div>
                  ) : (
                    <button 
                      type="button"
                      onClick={() => handleEdit(lowSupplyPx)}
                      className="relative z-20 cursor-pointer bg-white text-blue-600 px-8 py-3 rounded-full font-bold hover:bg-opacity-90 hover:scale-[1.02] transition-all shadow-sm active:scale-95 group/btn flex items-center justify-center gap-2"
                    >
                      <span className="relative z-30">
                        {parseInt(lowSupplyPx.supply || '0') <= 3 ? t('medicines.authorizeRefill') : t('medicines.updateStock')}
                      </span>
                      <Check className="w-5 h-5 opacity-0 group-hover/btn:opacity-100 transition-opacity relative z-30" />
                    </button>
                  )}
                  <button 
                    onClick={() => setIsRefillDismissed(true)}
                    className="bg-transparent border border-white/40 text-white px-8 py-3 rounded-full font-bold hover:bg-white/10 transition-all active:scale-95"
                  >
                    {t('medicines.dismiss')}
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </section>

        {/* Right Sidebar */}
        <section className="col-span-12 lg:col-span-4 space-y-8 h-full">
          <div className="bg-glass border-ghost rounded-[2.5rem] p-6 shadow-sm min-h-[400px]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-extrabold text-[#191c1e]">
                {showArchived ? t('medicines.archived') : t('medicines.active')}
              </h2>
              {showArchived && (
                <span className="text-[10px] font-black px-2 py-0.5 rounded bg-slate-100 text-slate-500 uppercase tracking-widest">
                  {t('medicines.historyMode')}
                </span>
              )}
            </div>
            
            {((showArchived ? archivedPrescriptions : activePrescriptions).length === 0) ? (
              <div className="py-12 border-2 border-dashed border-slate-100 rounded-[2rem] flex flex-col items-center justify-center text-center px-4">
                <LayoutGrid className="w-8 h-8 text-slate-200 mb-3" />
                <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest leading-relaxed">
                  {showArchived ? t('medicines.noArchived') : t('medicines.noActiveDesc')}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <AnimatePresence mode="popLayout">
                  {(showArchived ? archivedPrescriptions : activePrescriptions).map((px) => (
                    <motion.div 
                      key={px.id}
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      className={`backdrop-blur p-5 rounded-2xl border transition-all group shadow-sm hover:shadow-md cursor-pointer relative ${
                        showArchived ? 'bg-slate-50/50 border-slate-100' : 'bg-white/70 border-transparent hover:border-blue-600/20'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-4">
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase tracking-widest ${
                          px.category === 'primary' ? 'bg-blue-100 text-blue-600' :
                          px.category === 'tertiary' ? 'bg-orange-100 text-orange-600' : 'bg-slate-800 text-white'
                        }`}>
                          {px.type}
                        </span>
                        <div className="flex gap-2">
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                handleToggleArchive(px.id);
                              }}
                              className={`p-1.5 rounded-lg transition-colors ${showArchived ? 'text-blue-600 hover:bg-blue-50' : 'text-slate-400 hover:bg-slate-100'}`}
                              title={showArchived ? t('medicines.unarchive') : t('medicines.archiveRecord')}
                            >
                              <Calendar className="w-4 h-4" />
                            </button>
                        </div>
                      </div>
                      <h3 className="font-extrabold text-[#191c1e] text-lg group-hover:text-blue-600 transition-colors leading-tight">
                        {px.name}
                      </h3>
                      <p className="text-xs font-bold text-slate-500 mb-4 tracking-wide">{px.desc || t('global.generalHealthSupport')}</p>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-white/50 p-3 rounded-xl border border-slate-100/50 text-center">
                          <p className="text-[10px] uppercase font-black text-slate-400 tracking-widest mb-1">{t('medicines.dosage')}</p>
                          <p className="text-sm font-extrabold text-[#191c1e]">
                            {px.dosage || (px.name.includes(' ') ? px.name.split(' ').slice(1).join(' ') : '-')}
                          </p>
                        </div>
                        <div className="bg-white/50 p-3 rounded-xl border border-slate-100/50 text-center">
                          <p className="text-[10px] uppercase font-black text-slate-400 tracking-widest mb-1">{t('medicines.frequency')}</p>
                          <p className="text-sm font-extrabold text-[#191c1e]">{px.freq}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
            
            <button 
              onClick={() => setShowArchived(!showArchived)}
              className={`w-full mt-6 py-4 border-2 border-dashed rounded-2xl text-sm font-bold transition-all shadow-sm active:scale-[0.98] ${
                showArchived 
                ? 'border-blue-400 bg-blue-50 text-blue-700' 
                : 'border-slate-200 bg-slate-50/50 text-slate-500 hover:border-blue-300 hover:text-blue-600'
              }`}
            >
              {showArchived ? t('medicines.viewActive') : t('medicines.viewArchived')}
            </button>
          </div>

          {/* AI Insights Mini-Widget */}
          <div className="bg-slate-100 rounded-[2rem] p-6 border border-slate-200/50 shadow-inner">
            <div className="flex items-center gap-3 mb-4">
              <Bolt className="w-5 h-5 text-blue-600 fill-blue-600" />
              <h3 className="text-[10px] font-black uppercase tracking-widest text-[#191c1e]">{t('medicines.aiAdherence')}</h3>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                <svg className="w-full h-full transform -rotate-90 drop-shadow-sm">
                  <circle className="text-white" cx="32" cy="32" fill="transparent" r="28" stroke="currentColor" strokeWidth="6"></circle>
                  <circle 
                    className="text-blue-600 transition-all duration-1000" 
                    cx="32" 
                    cy="32" 
                    fill="transparent" 
                    r="28" 
                    stroke="currentColor" 
                    strokeDasharray="176" 
                    strokeDashoffset={176 - (176 * adherenceRate / 100)} 
                    strokeWidth="6" 
                    strokeLinecap="round"
                  ></circle>
                </svg>
                <span className="absolute text-[10px] font-black text-[#191c1e]">{adherenceRate}%</span>
              </div>
              <div>
                <p className="text-sm font-bold text-[#191c1e]">{adherenceRate > 80 ? t('medicines.excellent') : t('medicines.stable')}</p>
                <p className="text-[10px] font-bold text-slate-400 mt-0.5 leading-snug uppercase tracking-tight">{t('medicines.consistency')} • {completedCount}/{prescriptions.length}</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      <AddMedicineModal 
        isOpen={isAddModalOpen} 
        onClose={() => {
          setIsAddModalOpen(false);
          setEditingPx(null);
        }} 
        onSave={handleAddMedicine}
        pxToEdit={editingPx}
      />
    </div>
  );
}
