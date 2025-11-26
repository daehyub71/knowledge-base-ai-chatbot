import { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { LandingPage } from '@/components/landing/LandingPage';
import { ChatContainer } from '@/components/chat/ChatContainer';

type View = 'landing' | 'chat';

function App() {
  const [currentView, setCurrentView] = useState<View>('landing');

  return (
    <Layout>
      {currentView === 'landing' ? (
        <LandingPage onStartChat={() => setCurrentView('chat')} />
      ) : (
        <ChatContainer onBack={() => setCurrentView('landing')} />
      )}
    </Layout>
  );
}

export default App;
