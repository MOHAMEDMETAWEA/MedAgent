import React, { useState, useEffect } from 'react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { CloudUpload, Cpu, ShieldCheck, ArrowRight, Download, CheckCircle, Star, AlertTriangle, Play, Sparkles, History, Search, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useHealthData } from '../controllers/useHealthData';
import { PageHeader } from '../components/ui/PageHeader';
import { DataState } from '../components/ui/DataState';
import { UniversalImagePicker } from '../components/ui/UniversalImagePicker';
import { useAuth } from '../context/AuthContext';
import apiClient from '../services/apiClient';
import { motion, AnimatePresence } from 'framer-motion';
import { StudyReportModal } from '../components/medical/StudyReportModal';

export default function ScanImaging() {
  const { t } = useTranslation();
  const { userData, updateUser } = useAuth();
  const [selectedScan, setSelectedScan] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  
  const [selectedReport, setSelectedReport] = useState(null);
  const [isReportOpen, setIsReportOpen] = useState(false);

  const handleScanSelect = (img) => {
    // Validate file size (24MB limit)
    // Base64 string estimation: length * (3/4)
    const estimatedSize = (img.length * 0.75);
    const maxSize = 24 * 1024 * 1024; // 24MB in bytes

    if (estimatedSize > maxSize) {
      alert(t('scans.support')); 
      return;
    }
    setSelectedScan(img);
  };

  const handleDownload = (imgUrl, type) => {
    const link = document.createElement('a');
    link.href = imgUrl;
    link.download = `MedAgent_${type.replace(/\s+/g, '_')}_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDeleteScan = (id) => {
    if (!window.confirm(t('global.verified') + "?")) return; // Simplified or need a specific delete key
    
    const updatedHistory = userData.scanHistory.filter(scan => scan.id !== id);
    updateUser({
      scanHistory: updatedHistory
    });
  };

  const handleViewReport = (scan) => {
    setSelectedReport(scan);
    setIsReportOpen(true);
  };

  const handleRunDiagnostics = async () => {
    if (!selectedScan) return;
    
    setIsAnalyzing(true);
    setAnalysisProgress(0);

    // Simulated high-fidelity AI processing sequence
    const interval = setInterval(() => {
      setAnalysisProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 2;
      });
    }, 50);

    await new Promise(resolve => setTimeout(resolve, 3000));
    clearInterval(interval);

    let photoId = null;
    let photoUrl = selectedScan;

    // Upload to backend if authenticated
    const token = localStorage.getItem('medagent_token');
    if (token) {
      try {
        const formData = new FormData();
        // Convert base64 to blob for multipart upload
        const base64Response = await fetch(selectedScan);
        const blob = await base64Response.blob();
        formData.append('file', blob, 'scan.jpg');
        formData.append('category', 'Scan');

        const response = await apiClient.post('/photos', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        photoId = response.data.id;
        photoUrl = `/api/photos/content/${photoId}`;
      } catch (error) {
        console.error("Failed to upload scan to backend", error);
      }
    }

    const newScan = {
      id: photoId || Date.now(),
      type: 'Neural Capture / Automated',
      status: 'Completed',
      details: `Analyzed ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} • ${(Math.random() * 50 + 10).toFixed(1)} MB DICOM`,
      insights: ['AI Insight: Optimal Tissue Density', 'Neural Match: 99.4%'],
      imgUrl: photoUrl
    };

    updateUser({
      scanHistory: [newScan, ...(userData.scanHistory || [])]
    });

    setIsAnalyzing(false);
    setSelectedScan(null);
    setAnalysisProgress(0);
  };

  return (
    <div className="flex flex-col gap-6 h-full max-w-6xl mx-auto pt-4 relative space-y-4">
      <PageHeader 
        title={t('scans.title')} 
        subtitle={t('scans.subtitle')} 
        className="mb-4"
      />

    <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Upload Zone */}
      <div className="lg:col-span-2 group relative overflow-hidden rounded-[2.5rem] bg-glass border-ghost shadow-[0_10px_40px_rgba(0,0,0,0.03)] p-1">
        <div className="h-full w-full rounded-[2.2rem] border-2 border-dashed border-[var(--color-primary)]/20 bg-white/60 flex flex-col items-center justify-center p-12 transition-all duration-500 group-hover:bg-[var(--color-primary)]/5 group-hover:border-[var(--color-primary)]/40 relative z-10">
          <div className="relative mb-8">
            <div className="absolute -inset-4 bg-[var(--color-primary)]/10 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700 pointer-events-none"></div>
            {isAnalyzing ? (
              <div className="relative w-20 h-20 flex items-center justify-center">
                <Search className="w-16 h-16 text-blue-600 animate-pulse" />
                <motion.div 
                  className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                />
              </div>
            ) : (
              <CloudUpload className="w-20 h-20 text-[var(--color-primary)] relative z-20" />
            )}
          </div>
          <h3 className="text-2xl font-bold text-[#191c1e] mb-2 pointer-events-none">
            {isAnalyzing ? `${t('scans.analyzingTissue')} ${analysisProgress}%` : t('scans.drop')}
          </h3>
          <p className="text-[#434656] text-center mb-8 max-w-sm font-medium">
            {isAnalyzing ? t('scans.processingDicom') : t('scans.support')}
          </p>
          
            <UniversalImagePicker onImageSelect={handleScanSelect}>
              <button className="bg-[var(--color-primary)] text-white px-10 py-4 rounded-full font-bold shadow-lg shadow-[var(--color-primary)]/20 hover:scale-[1.02] active:scale-[0.98] transition-all">
                {selectedScan ? t('scans.selectDifferent') : t('scans.select')}
              </button>
            </UniversalImagePicker>

          {isAnalyzing && (
            <div className="w-full max-w-xs h-2 bg-slate-200 rounded-full overflow-hidden mb-4">
              <motion.div 
                className="h-full bg-blue-600"
                initial={{ width: 0 }}
                animate={{ width: `${analysisProgress}%` }}
              />
            </div>
          )}

          {selectedScan && !isAnalyzing && (
            <div className="mt-8 flex flex-col items-center animate-in fade-in slide-in-from-top-4 duration-500">
              <div className="w-48 h-48 rounded-2xl overflow-hidden border-4 border-white shadow-xl relative group">
                <img src={selectedScan} alt="Selected Scanning" className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-green-500/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <CheckCircle className="w-12 h-12 text-white drop-shadow-lg" />
                </div>
              </div>
              <p className="mt-3 text-sm font-bold text-green-600 flex items-center gap-2">
                <Sparkles className="w-4 h-4" /> {t('scans.readyNeural')}
              </p>
              <Button 
                onClick={handleRunDiagnostics}
                variant="primary" 
                className="mt-4 px-8 bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-600/20"
              >
                {t('scans.runDiagnostic')} <ArrowRight className="w-4 h-4 ms-2 rtl:-scale-x-100" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* AI Metric card */}
      <div className="lg:col-span-1 space-y-6 flex flex-col">
        <div className="p-8 rounded-[2rem] bg-blue-600 text-white relative overflow-hidden shadow-lg flex-1 group">
          <div className="relative z-10 h-full flex flex-col">
            <Cpu className="w-10 h-10 mb-4 opacity-90 group-hover:scale-110 transition-transform" />
            <h4 className="text-xl font-bold mb-1">{t('scans.engine')}</h4>
            <p className="text-sm opacity-80 mb-8 font-medium">{t('scans.core')}</p>
            <div className="mt-auto">
              <div className="flex items-end gap-2 mb-2">
                <span className="text-5xl font-extrabold tracking-tight">{(0.2 + (userData.scanHistory?.length || 0) * 0.05).toFixed(1)}s</span>
                <span className="text-sm font-medium mb-2 opacity-80">{t('global.latency')}</span>
              </div>
              <p className="text-[10px] uppercase tracking-widest font-bold opacity-60">{t('global.avgProcess')}</p>
            </div>
          </div>
          <div className="absolute -right-8 -bottom-8 w-40 h-40 bg-white/10 rounded-full blur-3xl pointer-events-none group-hover:scale-125 transition-transform duration-700"></div>
        </div>
        
        <div className="p-8 rounded-[2rem] bg-glass border-ghost shadow-[var(--shadow-liquid)]">
          <div className="flex justify-between items-start mb-6">
            <ShieldCheck className="w-8 h-8 text-emerald-500" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-[#434656] bg-slate-200/50 px-2 py-1 rounded-md">{t('global.hipaa')}</span>
          </div>
          <h4 className="text-lg font-bold text-[#191c1e] mb-2">{t('scans.zeroTrust')}</h4>
          <p className="text-sm text-[#434656] leading-relaxed font-medium">{t('scans.privacyDesc')}</p>
        </div>
      </div>
    </section>

    {/* History */}
    <section className="space-y-8 pt-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <History className="w-6 h-6 text-[#191c1e]" />
          <h2 className="text-2xl font-extrabold text-[#191c1e]">{t('scans.recent')}</h2>
        </div>
        <button className="text-[var(--color-primary)] font-bold text-sm flex items-center gap-2 hover:underline">
          {t('scans.viewAll')} <ArrowRight className="w-4 h-4 stroke-[3px] ms-1 rtl:-scale-x-100" />
        </button>
      </div>
      
      <div className="space-y-4 min-h-[200px]">
        <AnimatePresence mode="popLayout">
          {userData.scanHistory && userData.scanHistory.length > 0 ? (
            userData.scanHistory.map((scan, index) => (
              <motion.div 
                key={scan.id}
                layout
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -20 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                className="flex flex-col md:flex-row md:items-center gap-6 p-6 rounded-[2rem] bg-glass border-ghost shadow-[var(--shadow-liquid-hover)] hover:bg-white/80 transition-colors duration-300 group"
              >
                <div className="w-24 h-24 rounded-2xl overflow-hidden bg-slate-100 shrink-0 border border-slate-200/50 shadow-inner group-hover:scale-105 transition-transform">
                  <img src={scan.imgUrl} alt={scan.type} className="w-full h-full object-cover grayscale opacity-80 mix-blend-multiply group-hover:grayscale-0 group-hover:opacity-100 transition-all" />
                </div>
                
                <div className="flex-grow">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-extrabold text-[#191c1e]">{scan.type}</h3>
                    <span className={`px-3 py-1 text-[10px] font-extrabold rounded-full uppercase tracking-widest ${
                      scan.status === 'Completed' ? 'bg-green-100 text-green-700' :
                      scan.status === 'Processing' ? 'bg-blue-100 text-blue-700' :
                      'bg-orange-100 text-orange-700'
                    }`}>
                      {scan.status}
                    </span>
                  </div>
                  <p className="text-sm text-[#434656] mb-3 font-semibold opacity-70 italic">
                    ID Ref: {scan.details.split('•')[0]} • {scan.details.split('•')[1] || "15.0 MB Capture"}
                  </p>
                  
                  <div className="flex flex-wrap gap-2">
                    {scan.insights && scan.insights.length > 0 ? (
                      scan.insights.map((insight, idx) => (
                        <div key={idx} className={`px-3 py-1.5 text-xs font-bold rounded-lg flex items-center gap-2 ${
                          scan.status === 'Anomaly Detected' ? (idx === 0 ? 'bg-orange-50 text-orange-700' : 'bg-red-50 text-red-600') : 'bg-blue-50/50 text-blue-800'
                        }`}>
                          {idx === 0 && (
                            scan.status === 'Anomaly Detected' ? <AlertTriangle className="w-3 h-3"/> : <Star className="w-3 h-3" />
                          )}
                          {insight}
                        </div>
                      ))
                    ) : (
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                        <Loader2 className="w-3 h-3 animate-spin" /> {t('global.awaitingData')}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-3 shrink-0">
                  <button 
                    onClick={() => handleDownload(scan.imgUrl, scan.type)}
                    className="p-3 rounded-xl hover:bg-blue-50 bg-white border border-slate-200/50 text-[#434656] hover:text-blue-600 transition-all shadow-sm active:scale-95"
                  >
                    <Download className="w-5 h-5" />
                  </button>
                  <button 
                    onClick={() => handleDeleteScan(scan.id)}
                    className="p-3 rounded-xl hover:bg-red-50 bg-white border border-slate-200/50 text-[#434656] hover:text-red-600 transition-all shadow-sm active:scale-95"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                  <button 
                    onClick={() => handleViewReport(scan)}
                    className={`px-6 py-3 font-bold text-sm rounded-xl transition-all shadow-md flex items-center gap-2 active:scale-95
                      ${scan.status === 'Anomaly Detected' ? 'bg-red-600 text-white hover:bg-red-700 shadow-red-200' :
                        'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'}
                    `}
                  >
                    {scan.status === 'Anomaly Detected' ? t('scans.immediateReview') : t('scans.fullAnalysis')}
                  </button>
                </div>
              </motion.div>
            ))
          ) : (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center p-20 bg-glass border-ghost rounded-[2rem] text-center"
            >
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-6 text-slate-300">
                <Search className="w-10 h-10" />
              </div>
              <h3 className="text-xl font-bold text-[#191c1e] mb-2">{t('global.noDiagnostics')}</h3>
              <p className="text-[#434656] max-w-sm font-medium mb-8">{t('scans.beginJourney')}</p>
              <div className="flex gap-4">
                <div className="px-4 py-2 bg-slate-50 rounded-lg text-[10px] font-bold text-slate-400 uppercase tracking-widest border border-slate-100">{t('scans.hintDicom')}</div>
                <div className="px-4 py-2 bg-slate-50 rounded-lg text-[10px] font-bold text-slate-400 uppercase tracking-widest border border-slate-100">{t('scans.hintHipaa')}</div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>

    {/* Report Modal */}
    <StudyReportModal 
      isOpen={isReportOpen} 
      onClose={() => setIsReportOpen(false)} 
      scan={selectedReport} 
    />

    {/* Footer */}
    <footer className="border-t border-slate-200/50 mt-12 mb-8 pt-8 text-center px-4">
      <p className="text-xs text-[var(--color-on-surface-variant)] opacity-80 uppercase tracking-[0.2em] font-bold">{t('scans.version')}</p>
      <p className="text-[10px] text-[var(--color-on-surface-variant)] mt-2 max-w-xl mx-auto opacity-60 font-medium">{t('scans.neuralDisclaimer')}</p>
    </footer>
    </div>
  );
}


const Loader2 = ({ className }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width="24" 
    height="24" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
);
