import { useAuth } from '../context/AuthContext';

export function usePrescriptions() {
  const { userData, updateUser } = useAuth();
  const prescriptions = userData.prescriptions || [];

  const handleToggleStatus = (id) => {
    const updated = prescriptions.map(px => 
      px.id === id ? { ...px, status: px.status === 'completed' ? 'scheduled' : 'completed' } : px
    );
    updateUser({ prescriptions: updated });
  };

  const handleAddMedicine = (newPx, editingId = null) => {
    if (editingId) {
      const updated = prescriptions.map(px => px.id === editingId ? { ...newPx, id: editingId } : px);
      updateUser({ prescriptions: updated });
    } else {
      updateUser({ prescriptions: [...prescriptions, { ...newPx, id: Date.now() }] });
    }
  };

  const handleDelete = (id) => {
    const updated = prescriptions.filter(px => px.id !== id);
    updateUser({ prescriptions: updated });
  };

  const handleToggleArchive = (id) => {
    const updated = prescriptions.map(px => 
      String(px.id) === String(id) ? { ...px, archived: !px.archived } : px
    );
    updateUser({ prescriptions: updated });
  };

  const handleApproveRefill = (id) => {
    const updated = prescriptions.map(px => 
      String(px.id) === String(id) ? { ...px, status: 'refill_requested' } : px
    );
    updateUser({ prescriptions: updated });
  };

  const activePrescriptions = prescriptions.filter(px => !px.archived);
  const archivedPrescriptions = prescriptions.filter(px => px.archived);
  const pendingRefills = activePrescriptions.filter(px => parseInt(px.supply || '30') < 7 && px.status !== 'refill_requested');
  const authorizedRefills = activePrescriptions.filter(px => parseInt(px.supply || '30') < 7 && px.status === 'refill_requested');
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
