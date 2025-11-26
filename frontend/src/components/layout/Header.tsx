import { MessageSquare, Moon, Sun, LayoutDashboard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';

interface HeaderProps {
  onDashboardClick?: () => void;
}

export function Header({ onDashboardClick }: HeaderProps) {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    // Check system preference on mount
    const isDarkMode = document.documentElement.classList.contains('dark');
    setIsDark(isDarkMode);
  }, []);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-6 w-6 text-primary" />
          <span className="font-semibold text-lg">Knowledge Base AI</span>
        </div>

        <div className="flex flex-1 items-center justify-end space-x-2">
          {onDashboardClick && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDashboardClick}
              aria-label="Dashboard"
            >
              <LayoutDashboard className="h-4 w-4 mr-2" />
              Dashboard
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label="Toggle theme"
          >
            {isDark ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>
    </header>
  );
}
