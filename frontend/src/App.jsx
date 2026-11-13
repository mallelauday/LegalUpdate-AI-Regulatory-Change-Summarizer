import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import LiveScrapeModal from './components/LiveScrapeModal';

import LoginPage from './pages/LoginPage';
import DashboardOverviewPage from './pages/DashboardOverviewPage';
import RegulatoryUpdatesPage from './pages/RegulatoryUpdatesPage';
import UpdateDetailPage from './pages/UpdateDetailPage';
import AISummaryPage from './pages/AISummaryPage';
import HistoricalContextPage from './pages/HistoricalContextPage';
import ReviewQueuePage from './pages/ReviewQueuePage';
import SourceManagementPage from './pages/SourceManagementPage';
import UserManagementPage from './pages/UserManagementPage';
import SettingsPage from './pages/SettingsPage';

function AppContent() {
  const { user, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedUpdateId, setSelectedUpdateId] = useState(null);
  const [isScrapeOpen, setIsScrapeOpen] = useState(false);

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0f172a',
        color: '#f8fafc',
        fontFamily: 'sans-serif'
      }}>
        Initializing LegalUpdate AI Workspace...
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const handleSelectUpdate = (updateId) => {
    setSelectedUpdateId(updateId);
    setCurrentPage('detail');
  };

  const getPageTitle = () => {
    switch (currentPage) {
      case 'dashboard': return 'Dashboard Overview';
      case 'updates': return 'Regulatory Updates Feed';
      case 'detail': return 'Document Legal Inspection';
      case 'summary': return 'AI Regulatory Summaries Gallery';
      case 'history': return 'Memento Historical Memory Explorer';
      case 'review': return 'Legal Review & Approval Workbench';
      case 'sources': return 'Official Regulatory Source Management';
      case 'users': return 'User Access & Authorization';
      case 'settings': return 'System Settings & Integrations';
      default: return 'LegalUpdate AI';
    }
  };

  return (
    <div className="app-container">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      
      <div className="main-content">
        <Navbar 
          title={getPageTitle()} 
          onOpenScrapeModal={() => setIsScrapeOpen(true)} 
        />
        
        <main className="page-body">
          {currentPage === 'dashboard' && (
            <DashboardOverviewPage 
              onSelectUpdate={handleSelectUpdate}
              onOpenScrapeModal={() => setIsScrapeOpen(true)}
            />
          )}

          {currentPage === 'updates' && (
            <RegulatoryUpdatesPage 
              onSelectUpdate={handleSelectUpdate}
              onOpenScrapeModal={() => setIsScrapeOpen(true)}
            />
          )}

          {currentPage === 'detail' && (
            <UpdateDetailPage 
              updateId={selectedUpdateId}
              onBack={() => setCurrentPage('updates')}
            />
          )}

          {currentPage === 'summary' && (
            <AISummaryPage onSelectUpdate={handleSelectUpdate} />
          )}

          {currentPage === 'history' && (
            <HistoricalContextPage onSelectUpdate={handleSelectUpdate} />
          )}

          {currentPage === 'review' && (
            <ReviewQueuePage onSelectUpdate={handleSelectUpdate} />
          )}

          {currentPage === 'sources' && (
            <SourceManagementPage />
          )}

          {currentPage === 'users' && (
            <UserManagementPage />
          )}

          {currentPage === 'settings' && (
            <SettingsPage />
          )}
        </main>
      </div>

      <LiveScrapeModal
        isOpen={isScrapeOpen}
        onClose={() => setIsScrapeOpen(false)}
        onSuccess={(data) => {
          if (data?.update_id) {
            setSelectedUpdateId(data.update_id);
            setCurrentPage('detail');
          }
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
