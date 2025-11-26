import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { CheckCircle, AlertCircle, FileText, Clock } from 'lucide-react';

interface DataSourceCardProps {
  source: 'jira' | 'confluence';
  status: 'healthy' | 'error' | 'syncing';
  docsCount: number;
  lastSync: string;
}

export function DataSourceCard({ source, status, docsCount, lastSync }: DataSourceCardProps) {
  const sourceConfig = {
    jira: {
      name: 'Jira',
      color: 'bg-blue-500',
      logo: '🎫',
    },
    confluence: {
      name: 'Confluence',
      color: 'bg-blue-600',
      logo: '📄',
    },
  };

  const statusConfig = {
    healthy: {
      label: 'Healthy',
      icon: CheckCircle,
      className: 'text-green-500',
      badgeClass: 'bg-green-500/20 text-green-500 border-green-500/30',
    },
    error: {
      label: 'Error',
      icon: AlertCircle,
      className: 'text-red-500',
      badgeClass: 'bg-red-500/20 text-red-500 border-red-500/30',
    },
    syncing: {
      label: 'Syncing',
      icon: Clock,
      className: 'text-yellow-500',
      badgeClass: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
    },
  };

  const config = sourceConfig[source];
  const statusInfo = statusConfig[status];
  const StatusIcon = statusInfo.icon;

  return (
    <Card className="bg-card border-border">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Logo */}
          <div className={cn(
            'flex items-center justify-center w-12 h-12 rounded-lg text-2xl',
            config.color
          )}>
            {config.logo}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-foreground">{config.name}</h3>
              <span className={cn(
                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border',
                statusInfo.badgeClass
              )}>
                <StatusIcon className="h-3 w-3" />
                {statusInfo.label}
              </span>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-4">
              <div>
                <div className="flex items-center gap-1 text-muted-foreground text-xs">
                  <FileText className="h-3 w-3" />
                  Documents Synced
                </div>
                <p className="text-lg font-semibold text-foreground mt-1">
                  {docsCount.toLocaleString()}
                </p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-muted-foreground text-xs">
                  <Clock className="h-3 w-3" />
                  Last Sync
                </div>
                <p className="text-sm text-foreground mt-1">
                  {lastSync}
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
