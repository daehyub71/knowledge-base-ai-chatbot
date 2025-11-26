import type { ReactNode } from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
  onDashboardClick?: () => void;
}

export function Layout({ children, onDashboardClick }: LayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Header onDashboardClick={onDashboardClick} />
      <main className="container mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}
