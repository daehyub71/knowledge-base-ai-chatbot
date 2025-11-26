import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, CheckCircle, AlertCircle, Clock, Calendar } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  status?: 'healthy' | 'error' | 'warning';
  type?: 'status' | 'count' | 'time' | 'schedule';
}

export function StatCard({ label, value, change, status, type = 'count' }: StatCardProps) {
  const getStatusBadge = () => {
    if (!status) return null;

    const styles = {
      healthy: 'bg-green-500/20 text-green-500 border-green-500/30',
      error: 'bg-red-500/20 text-red-500 border-red-500/30',
      warning: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
    };

    const icons = {
      healthy: <CheckCircle className="h-3 w-3" />,
      error: <AlertCircle className="h-3 w-3" />,
      warning: <AlertCircle className="h-3 w-3" />,
    };

    return (
      <span className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border',
        styles[status]
      )}>
        {icons[status]}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getIcon = () => {
    switch (type) {
      case 'status':
        return <CheckCircle className="h-5 w-5 text-muted-foreground" />;
      case 'count':
        return <TrendingUp className="h-5 w-5 text-muted-foreground" />;
      case 'time':
        return <Clock className="h-5 w-5 text-muted-foreground" />;
      case 'schedule':
        return <Calendar className="h-5 w-5 text-muted-foreground" />;
      default:
        return null;
    }
  };

  return (
    <Card className="bg-card border-border">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{label}</p>
            <div className="flex items-center gap-2">
              {type === 'status' && status ? (
                getStatusBadge()
              ) : (
                <p className="text-2xl font-bold text-foreground">{value}</p>
              )}
            </div>
            {change !== undefined && (
              <div className={cn(
                'flex items-center gap-1 text-xs',
                change >= 0 ? 'text-green-500' : 'text-red-500'
              )}>
                {change >= 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                <span>{change >= 0 ? '+' : ''}{change}%</span>
                <span className="text-muted-foreground">vs last week</span>
              </div>
            )}
          </div>
          {getIcon()}
        </div>
      </CardContent>
    </Card>
  );
}
