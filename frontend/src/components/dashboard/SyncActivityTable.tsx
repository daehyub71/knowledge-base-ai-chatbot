import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

interface SyncActivity {
  id: string;
  timestamp: string;
  eventType: string;
  status: 'success' | 'failed' | 'in_progress';
  description: string;
}

interface SyncActivityTableProps {
  activities: SyncActivity[];
}

export function SyncActivityTable({ activities }: SyncActivityTableProps) {
  const statusConfig = {
    success: {
      label: 'Success',
      icon: CheckCircle,
      className: 'bg-green-500/20 text-green-500 border-green-500/30',
    },
    failed: {
      label: 'Failed',
      icon: AlertCircle,
      className: 'bg-red-500/20 text-red-500 border-red-500/30',
    },
    in_progress: {
      label: 'In Progress',
      icon: RefreshCw,
      className: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
    },
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium text-foreground">
          Recent Sync Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="text-left py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Event Type
                </th>
                <th className="text-left py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left py-3 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody>
              {activities.map((activity) => {
                const status = statusConfig[activity.status];
                const StatusIcon = status.icon;
                return (
                  <tr
                    key={activity.id}
                    className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors"
                  >
                    <td className="py-3 px-2 text-sm text-muted-foreground">
                      {activity.timestamp}
                    </td>
                    <td className="py-3 px-2 text-sm text-foreground font-medium">
                      {activity.eventType}
                    </td>
                    <td className="py-3 px-2">
                      <span className={cn(
                        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border',
                        status.className
                      )}>
                        <StatusIcon className={cn(
                          'h-3 w-3',
                          activity.status === 'in_progress' && 'animate-spin'
                        )} />
                        {status.label}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-sm text-muted-foreground">
                      {activity.description}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
