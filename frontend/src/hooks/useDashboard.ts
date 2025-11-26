import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStats } from '@/services/api';

interface DashboardStats {
  overallStatus: 'healthy' | 'error' | 'warning';
  totalDocuments: number;
  documentsChange: number;
  lastSync: string;
  nextSync: string;
}

interface DataSource {
  type: 'jira' | 'confluence';
  status: 'healthy' | 'error' | 'syncing';
  docsCount: number;
  lastSync: string;
}

interface ChartDataPoint {
  date: string;
  documents: number;
}

interface SyncActivity {
  id: string;
  timestamp: string;
  eventType: string;
  status: 'success' | 'failed' | 'in_progress';
  description: string;
}

// Mock data generator for demo
function generateMockData() {
  const now = new Date();

  // Generate last 7 days chart data
  const chartData: ChartDataPoint[] = [];
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    chartData.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      documents: Math.floor(Math.random() * 50) + 100,
    });
  }

  // Generate recent activities
  const activities: SyncActivity[] = [
    {
      id: '1',
      timestamp: new Date(now.getTime() - 5 * 60000).toLocaleString(),
      eventType: 'Full Sync',
      status: 'success',
      description: 'Successfully synced 45 documents from Jira',
    },
    {
      id: '2',
      timestamp: new Date(now.getTime() - 35 * 60000).toLocaleString(),
      eventType: 'Incremental Sync',
      status: 'success',
      description: 'Synced 12 updated documents from Confluence',
    },
    {
      id: '3',
      timestamp: new Date(now.getTime() - 65 * 60000).toLocaleString(),
      eventType: 'Full Sync',
      status: 'failed',
      description: 'Connection timeout to Jira API',
    },
    {
      id: '4',
      timestamp: new Date(now.getTime() - 125 * 60000).toLocaleString(),
      eventType: 'Incremental Sync',
      status: 'success',
      description: 'Synced 8 new documents from Confluence',
    },
  ];

  return { chartData, activities };
}

export function useDashboard() {
  const [error, setError] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  // Fetch stats from backend
  const {
    data: statsData,
    isLoading,
    isRefetching: isRefreshing,
    refetch,
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getStats,
    refetchInterval: 30000, // Auto refresh every 30 seconds
  });

  // Generate mock data for demo
  const { chartData, activities } = generateMockData();

  // Calculate stats from API response
  const stats: DashboardStats = {
    overallStatus: 'healthy',
    totalDocuments: statsData?.total_documents || 0,
    documentsChange: 12, // Mock value
    lastSync: statsData?.last_sync || new Date().toLocaleString(),
    nextSync: new Date(Date.now() + 30 * 60000).toLocaleString(),
  };

  // Data sources based on stats
  const dataSources: DataSource[] = [
    {
      type: 'jira',
      status: 'healthy',
      docsCount: statsData?.by_type?.jira || 0,
      lastSync: '5 minutes ago',
    },
    {
      type: 'confluence',
      status: 'healthy',
      docsCount: statsData?.by_type?.confluence || 0,
      lastSync: '5 minutes ago',
    },
  ];

  // Refresh handler
  const refresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Trigger sync handler
  const triggerSync = useCallback(async () => {
    setIsSyncing(true);
    try {
      // TODO: Call actual sync API
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await refetch();
    } catch (err) {
      setError('Failed to trigger sync. Please try again.');
    } finally {
      setIsSyncing(false);
    }
  }, [refetch]);

  // Dismiss error
  const dismissError = useCallback(() => {
    setError(null);
  }, []);

  return {
    stats,
    dataSources,
    chartData,
    activities,
    error,
    isLoading,
    isRefreshing,
    isSyncing,
    refresh,
    triggerSync,
    dismissError,
  };
}
