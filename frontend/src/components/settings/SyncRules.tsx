import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, Loader2 } from 'lucide-react';

interface SyncRulesProps {
  incrementalSync: boolean;
  syncFrequency: '6h' | '12h' | '24h' | 'manual';
  lastSynced?: string;
  onIncrementalChange: (enabled: boolean) => void;
  onFrequencyChange: (frequency: '6h' | '12h' | '24h' | 'manual') => void;
  onSyncNow: () => void;
  isSyncing?: boolean;
}

export function SyncRules({
  incrementalSync,
  syncFrequency,
  lastSynced,
  onIncrementalChange,
  onFrequencyChange,
  onSyncNow,
  isSyncing = false,
}: SyncRulesProps) {
  const frequencyOptions = [
    { value: '6h' as const, label: 'Every 6 hours' },
    { value: '12h' as const, label: 'Every 12 hours' },
    { value: '24h' as const, label: 'Every 24 hours' },
    { value: 'manual' as const, label: 'Manual only' },
  ];

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-medium text-foreground">
          Sync Rules
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Incremental Sync Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">Incremental Sync</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Only sync new or updated documents
            </p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={incrementalSync}
            onClick={() => onIncrementalChange(!incrementalSync)}
            className={`
              relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent
              transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2
              focus-visible:ring-primary focus-visible:ring-offset-2
              ${incrementalSync ? 'bg-primary' : 'bg-muted'}
            `}
          >
            <span
              className={`
                pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg
                ring-0 transition duration-200 ease-in-out
                ${incrementalSync ? 'translate-x-5' : 'translate-x-0'}
              `}
            />
          </button>
        </div>

        {/* Sync Frequency */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Sync Frequency</label>
          <select
            value={syncFrequency}
            onChange={(e) => onFrequencyChange(e.target.value as '6h' | '12h' | '24h' | 'manual')}
            className="w-full h-10 px-3 rounded-md border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {frequencyOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Last Synced & Sync Now */}
        <div className="flex items-center justify-between pt-2">
          <div>
            <p className="text-xs text-muted-foreground">Last Synced</p>
            <p className="text-sm text-foreground">
              {lastSynced || 'Never'}
            </p>
          </div>
          <Button
            size="sm"
            onClick={onSyncNow}
            disabled={isSyncing}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            {isSyncing ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            {isSyncing ? 'Syncing...' : 'Sync Now'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
