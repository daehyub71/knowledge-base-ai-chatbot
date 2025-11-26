import { useState } from 'react';
import { Save } from 'lucide-react';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Button } from '@/components/ui/button';
import { AlertBanner } from '@/components/dashboard/AlertBanner';
import { DataSourceTabs } from '@/components/settings/DataSourceTabs';
import { ConnectionStatus } from '@/components/settings/ConnectionStatus';
import { ConnectionSettings } from '@/components/settings/ConnectionSettings';
import { SyncRules } from '@/components/settings/SyncRules';
import { useSettings } from '@/hooks/useSettings';

interface SettingsPageProps {
  onNavigate: (page: 'dashboard' | 'sources' | 'settings' | 'logs' | 'chat') => void;
}

export function SettingsPage({ onNavigate }: SettingsPageProps) {
  const [activeTab, setActiveTab] = useState<'jira' | 'confluence'>('jira');

  const {
    jiraConfig,
    confluenceConfig,
    syncSettings,
    connectionStatus,
    error,
    isSaving,
    isSyncing,
    updateJiraConfig,
    updateConfluenceConfig,
    updateSyncSettings,
    testConnection,
    saveChanges,
    triggerSync,
    dismissError,
  } = useSettings();

  const currentConfig = activeTab === 'jira' ? jiraConfig : confluenceConfig;
  const updateConfig = activeTab === 'jira' ? updateJiraConfig : updateConfluenceConfig;

  return (
    <AdminLayout currentPage="settings" onNavigate={onNavigate}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Data Source Management
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Configure your Jira and Confluence connections for document synchronization
            </p>
          </div>
          <Button
            onClick={saveChanges}
            disabled={isSaving}
            className="bg-primary hover:bg-primary/90"
          >
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>

        {/* Error Banner */}
        {error && (
          <AlertBanner
            type="error"
            title="Configuration Error"
            message={error}
            onClose={dismissError}
          />
        )}

        {/* Data Source Tabs */}
        <DataSourceTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {/* Content */}
        <div className="space-y-6">
          {/* Connection Status */}
          <ConnectionStatus
            status={connectionStatus[activeTab]}
            message={
              connectionStatus[activeTab] === 'connected'
                ? 'Successfully connected to Atlassian'
                : connectionStatus[activeTab] === 'error'
                ? 'Unable to connect. Check your credentials.'
                : 'Waiting for configuration'
            }
          />

          {/* Connection Settings */}
          <ConnectionSettings
            source={activeTab}
            config={currentConfig}
            onUpdate={updateConfig}
            onTestConnection={() => testConnection(activeTab)}
          />

          {/* Sync Rules */}
          <SyncRules
            incrementalSync={syncSettings.incrementalSync}
            syncFrequency={syncSettings.frequency}
            lastSynced={syncSettings.lastSynced}
            onIncrementalChange={(enabled) =>
              updateSyncSettings({ ...syncSettings, incrementalSync: enabled })
            }
            onFrequencyChange={(frequency) =>
              updateSyncSettings({ ...syncSettings, frequency })
            }
            onSyncNow={triggerSync}
            isSyncing={isSyncing}
          />
        </div>
      </div>
    </AdminLayout>
  );
}
