import { RefreshCw, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface DashboardHeaderProps {
  onRefresh: () => void;
  onSyncNow: () => void;
  isRefreshing?: boolean;
  isSyncing?: boolean;
}

export function DashboardHeader({
  onRefresh,
  onSyncNow,
  isRefreshing = false,
  isSyncing = false,
}: DashboardHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Data Synchronization Dashboard
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Monitor and manage your Jira and Confluence data synchronization
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw className={cn('h-4 w-4 mr-2', isRefreshing && 'animate-spin')} />
          Refresh Status
        </Button>
        <Button
          size="sm"
          onClick={onSyncNow}
          disabled={isSyncing}
          className="bg-orange-500 hover:bg-orange-600 text-white"
        >
          <Play className={cn('h-4 w-4 mr-2', isSyncing && 'animate-pulse')} />
          {isSyncing ? 'Syncing...' : 'Sync Now'}
        </Button>
      </div>
    </div>
  );
}
