import { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { LandingPage } from '@/components/landing/LandingPage';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { DashboardPage } from '@/pages/DashboardPage';
import { SettingsPage } from '@/pages/SettingsPage';

type View = 'landing' | 'chat' | 'dashboard' | 'sources' | 'settings' | 'logs';

function App() {
  const [currentView, setCurrentView] = useState<View>('landing');

  const handleAdminNavigate = (page: 'dashboard' | 'sources' | 'settings' | 'logs' | 'chat') => {
    if (page === 'chat') {
      setCurrentView('chat');
    } else {
      setCurrentView(page);
    }
  };

  // Settings page
  if (currentView === 'settings' || currentView === 'sources') {
    return <SettingsPage onNavigate={handleAdminNavigate} />;
  }

  // Dashboard and other admin views
  if (currentView === 'dashboard' || currentView === 'logs') {
    return <DashboardPage onNavigate={handleAdminNavigate} />;
  }

  // Main user views with Layout
  return (
    <Layout onDashboardClick={() => setCurrentView('dashboard')}>
      {currentView === 'landing' ? (
        <LandingPage onStartChat={() => setCurrentView('chat')} />
      ) : (
        <ChatContainer onBack={() => setCurrentView('landing')} />
      )}
    </Layout>
  );
}

export default App;
