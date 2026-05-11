import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './theme/theme.css';
import './i18n/config';

import { AuthProvider } from './context/AuthContext';
import { EmergencyProvider } from './context/EmergencyContext';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <EmergencyProvider>
          <App />
        </EmergencyProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
