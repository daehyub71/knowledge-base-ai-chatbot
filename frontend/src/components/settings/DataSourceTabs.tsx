import { cn } from '@/lib/utils';

interface DataSourceTabsProps {
  activeTab: 'jira' | 'confluence';
  onTabChange: (tab: 'jira' | 'confluence') => void;
}

export function DataSourceTabs({ activeTab, onTabChange }: DataSourceTabsProps) {
  const tabs = [
    { id: 'jira' as const, label: 'Jira', emoji: '🎫' },
    { id: 'confluence' as const, label: 'Confluence', emoji: '📄' },
  ];

  return (
    <div className="border-b border-border">
      <nav className="flex gap-4" aria-label="Data source tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              'relative py-3 px-1 text-sm font-medium transition-colors',
              activeTab === tab.id
                ? 'text-primary'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <span className="flex items-center gap-2">
              <span>{tab.emoji}</span>
              {tab.label}
            </span>
            {activeTab === tab.id && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
        ))}
      </nav>
    </div>
  );
}
