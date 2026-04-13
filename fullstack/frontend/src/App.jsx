import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { TopNavLayout } from './components/TopNavLayout';
import ChatDashboard from './pages/ChatDashboard';
import Medicines from './pages/Medicines';
import MedicalID from './pages/MedicalID';
import ScanImaging from './pages/ScanImaging';
import Emergency from './pages/Emergency';
import ContactDoctor from './pages/ContactDoctor';
import SharedInsurance from './pages/SharedInsurance';

import { ProtectedRoute } from './components/ProtectedRoute';

function App() {
  return (
    <Routes>
      <Route path="/" element={<TopNavLayout />}>
        {/* Public Pages */}
        <Route index element={<ChatDashboard />} />
        <Route path="contact" element={<ContactDoctor />} />
        <Route path="scans" element={<ScanImaging />} />
        <Route path="scan-imaging" element={<ScanImaging />} />
        <Route path="emergency" element={<Emergency />} />
        
        {/* Secure Pages (Login Required) */}
        <Route path="medicines" element={<ProtectedRoute><Medicines /></ProtectedRoute>} />
        <Route path="id" element={<ProtectedRoute><MedicalID /></ProtectedRoute>} />
      </Route>

      {/* Public Standalone Pages */}
      <Route path="share/insurance-:id" element={<SharedInsurance />} />
    </Routes>
  );
}

export default App;
