import { useState, useCallback } from 'react';

interface ConnectionConfig {
  instanceType: 'cloud' | 'server';
  url: string;
  token: string;
}

interface SyncSettings {
  incrementalSync: boolean;
  frequency: '6h' | '12h' | '24h' | 'manual';
  lastSynced?: string;
}

interface ConnectionStatuses {
  jira: 'connected' | 'error' | 'pending';
  confluence: 'connected' | 'error' | 'pending';
}

// Default configurations
const defaultJiraConfig: ConnectionConfig = {
  instanceType: 'cloud',
  url: '',
  token: '',
};

const defaultConfluenceConfig: ConnectionConfig = {
  instanceType: 'cloud',
  url: '',
  token: '',
};

const defaultSyncSettings: SyncSettings = {
  incrementalSync: true,
  frequency: '12h',
  lastSynced: undefined,
};

export function useSettings() {
  // State
  const [jiraConfig, setJiraConfig] = useState<ConnectionConfig>(defaultJiraConfig);
  const [confluenceConfig, setConfluenceConfig] = useState<ConnectionConfig>(defaultConfluenceConfig);
  const [syncSettings, setSyncSettings] = useState<SyncSettings>(defaultSyncSettings);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatuses>({
    jira: 'pending',
    confluence: 'pending',
  });
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // Update handlers
  const updateJiraConfig = useCallback((config: ConnectionConfig) => {
    setJiraConfig(config);
    // Reset connection status when config changes
    setConnectionStatus((prev) => ({ ...prev, jira: 'pending' }));
  }, []);

  const updateConfluenceConfig = useCallback((config: ConnectionConfig) => {
    setConfluenceConfig(config);
    setConnectionStatus((prev) => ({ ...prev, confluence: 'pending' }));
  }, []);

  const updateSyncSettings = useCallback((settings: SyncSettings) => {
    setSyncSettings(settings);
  }, []);

  // Test connection
  const testConnection = useCallback(async (source: 'jira' | 'confluence') => {
    const config = source === 'jira' ? jiraConfig : confluenceConfig;

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Mock validation
    if (!config.url || !config.token) {
      setConnectionStatus((prev) => ({ ...prev, [source]: 'error' }));
      return { success: false, message: 'URL and token are required' };
    }

    // Simulate success/failure (80% success rate for demo)
    const success = Math.random() > 0.2;

    setConnectionStatus((prev) => ({
      ...prev,
      [source]: success ? 'connected' : 'error',
    }));

    return {
      success,
      message: success ? 'Connection successful!' : 'Failed to connect. Check credentials.',
    };
  }, [jiraConfig, confluenceConfig]);

  // Save changes
  const saveChanges = useCallback(async () => {
    setIsSaving(true);
    setError(null);

    try {
      // TODO: Call actual save API
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Simulate success
      console.log('Settings saved:', { jiraConfig, confluenceConfig, syncSettings });
    } catch {
      setError('Failed to save settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  }, [jiraConfig, confluenceConfig, syncSettings]);

  // Trigger sync
  const triggerSync = useCallback(async () => {
    setIsSyncing(true);
    setError(null);

    try {
      // TODO: Call actual sync API
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Update last synced time
      setSyncSettings((prev) => ({
        ...prev,
        lastSynced: new Date().toLocaleString(),
      }));
    } catch {
      setError('Sync failed. Please check your connection settings.');
    } finally {
      setIsSyncing(false);
    }
  }, []);

  // Dismiss error
  const dismissError = useCallback(() => {
    setError(null);
  }, []);

  return {
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
  };
}
