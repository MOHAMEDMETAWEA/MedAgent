import { useState, useEffect } from 'react';
import apiClient from '../services/apiClient';
import { useAuth } from '../context/AuthContext';

export function usePrescriptions() {
  const { isAuthenticated } = useAuth();
  const [medicines, setMedicines] = useState([]);

  useEffect(() => {
    if (!isAuthenticated) return;
    apiClient.get('/medicines')
      .then(res => setMedicines(res.data || []))
      .catch(() => {});
  }, [isAuthenticated]);

  const handleToggleStatus = async (id) => {
    const px = medicines.find(m => String(m.id) === String(id));
    if (!px) return;
    const updated = { ...px, status: px.status === 'completed' ? 'scheduled' : 'completed' };
    try {
      const res = await apiClient.put(`/medicines/${id}`, updated);
      setMedicines(prev => prev.map(m => String(m.id) === String(id) ? res.data : m));
    } catch {}
  };

  const handleAddMedicine = async (newPx, editingId = null) => {
    try {
      if (editingId) {
        const res = await apiClient.put(`/medicines/${editingId}`, newPx);
        setMedicines(prev => prev.map(m => String(m.id) === String(editingId) ? res.data : m));
      } else {
        const { id: _ignored, ...payload } = newPx;
        const res = await apiClient.post('/medicines', payload);
        setMedicines(prev => [...prev, res.data]);
      }
    } catch (err) {
      console.error('Failed to save medicine:', err.response?.data ?? err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/medicines/${id}`);
      setMedicines(prev => prev.filter(m => String(m.id) !== String(id)));
    } catch {}
  };

  const handleToggleArchive = async (id) => {
    const px = medicines.find(m => String(m.id) === String(id));
    if (!px) return;
    const updated = { ...px, archived: !px.archived };
    try {
      const res = await apiClient.put(`/medicines/${id}`, updated);
      setMedicines(prev => prev.map(m => String(m.id) === String(id) ? res.data : m));
    } catch {}
  };

  const handleApproveRefill = async (id) => {
    const px = medicines.find(m => String(m.id) === String(id));
    if (!px) return;
    const updated = { ...px, status: 'refill_requested' };
    try {
      const res = await apiClient.put(`/medicines/${id}`, updated);
      setMedicines(prev => prev.map(m => String(m.id) === String(id) ? res.data : m));
    } catch {}
  };

  const prescriptions = medicines;
  const activePrescriptions = medicines.filter(m => !m.archived);
  const archivedPrescriptions = medicines.filter(m => m.archived);
  const pendingRefills = activePrescriptions.filter(m => parseInt(m.supply || '30') < 7 && m.status !== 'refill_requested');
  const authorizedRefills = activePrescriptions.filter(m => parseInt(m.supply || '30') < 7 && m.status === 'refill_requested');
  const lowSupplyPx = pendingRefills[0] || authorizedRefills[0];

  return {
    prescriptions,
    activePrescriptions,
    archivedPrescriptions,
    pendingRefills,
    authorizedRefills,
    lowSupplyPx,
    handleToggleStatus,
    handleAddMedicine,
    handleDelete,
    handleToggleArchive,
    handleApproveRefill
  };
}
