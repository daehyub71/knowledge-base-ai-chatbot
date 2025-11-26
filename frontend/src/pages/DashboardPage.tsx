import { AdminLayout } from '@/components/layout/AdminLayout';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { StatCard } from '@/components/dashboard/StatCard';
import { AlertBanner } from '@/components/dashboard/AlertBanner';
import { DataSourceCard } from '@/components/dashboard/DataSourceCard';
import { SyncChart } from '@/components/dashboard/SyncChart';
import { SyncActivityTable } from '@/components/dashboard/SyncActivityTable';
import { useDashboard } from '@/hooks/useDashboard';

interface DashboardPageProps {
  onNavigate: (page: 'dashboard' | 'sources' | 'settings' | 'logs' | 'chat') => void;
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const {
    stats,
    dataSources,
    chartData,
    activities,
    error,
    isRefreshing,
    isSyncing,
    refresh,
    triggerSync,
    dismissError,
  } = useDashboard();

  return (
    <AdminLayout currentPage="dashboard" onNavigate={onNavigate}>
      <div className="space-y-6">
        {/* Header */}
        <DashboardHeader
          onRefresh={refresh}
          onSyncNow={triggerSync}
          isRefreshing={isRefreshing}
          isSyncing={isSyncing}
        />

        {/* Error Banner */}
        {error && (
          <AlertBanner
            type="error"
            title="Sync Error Detected"
            message={error}
            linkText="View Full Logs"
            onLinkClick={() => onNavigate('logs')}
            onClose={dismissError}
          />
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Overall Sync Status"
            value=""
            status={stats.overallStatus}
            type="status"
          />
          <StatCard
            label="Total Documents Synced"
            value={stats.totalDocuments.toLocaleString()}
            change={stats.documentsChange}
            type="count"
          />
          <StatCard
            label="Last Successful Sync"
            value={stats.lastSync}
            type="time"
          />
          <StatCard
            label="Next Scheduled Sync"
            value={stats.nextSync}
            type="schedule"
          />
        </div>

        {/* Data Sources */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4">Data Sources</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dataSources.map((source) => (
              <DataSourceCard
                key={source.type}
                source={source.type}
                status={source.status}
                docsCount={source.docsCount}
                lastSync={source.lastSync}
              />
            ))}
          </div>
        </div>

        {/* Chart */}
        <SyncChart data={chartData} />

        {/* Activity Table */}
        <SyncActivityTable activities={activities} />
      </div>
    </AdminLayout>
  );
}
