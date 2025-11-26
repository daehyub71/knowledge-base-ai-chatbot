import type { ReactNode } from 'react';
import { LayoutDashboard, Database, Settings, FileText, MessageSquare, Moon, Sun, User } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AdminLayoutProps {
  children: ReactNode;
  currentPage: 'dashboard' | 'sources' | 'settings' | 'logs' | 'chat';
  onNavigate: (page: 'dashboard' | 'sources' | 'settings' | 'logs' | 'chat') => void;
}

const navItems = [
  { id: 'dashboard' as const, label: 'Dashboard', icon: LayoutDashboard },
  { id: 'sources' as const, label: 'Data Sources', icon: Database },
  { id: 'settings' as const, label: 'Settings', icon: Settings },
  { id: 'logs' as const, label: 'Logs', icon: FileText },
  { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
];

export function AdminLayout({ children, currentPage, onNavigate }: AdminLayoutProps) {
  const toggleTheme = () => {
    document.documentElement.classList.toggle('dark');
  };

  const isDark = document.documentElement.classList.contains('dark');

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4">
          <div className="flex h-14 items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <Database className="h-6 w-6 text-primary" />
              <span className="font-semibold text-foreground">Knowledge Base AI</span>
            </div>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <Button
                    key={item.id}
                    variant={isActive ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => onNavigate(item.id)}
                    className={isActive ? 'bg-secondary' : ''}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.label}
                  </Button>
                );
              })}
            </nav>

            {/* Right side */}
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" onClick={toggleTheme}>
                {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </Button>
              <Button variant="ghost" size="icon">
                <User className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}
