import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity } from 'lucide-react';

export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Activity className="w-10 h-10 text-[var(--color-primary)] animate-pulse" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect unauthenticated users to the Home/Diagnose page (or login modal)
    // We pass state so they can be redirected back after successful login
    return <Navigate to="/" state={{ from: location, openAuthModal: true }} replace />;
  }

  return children;
}
