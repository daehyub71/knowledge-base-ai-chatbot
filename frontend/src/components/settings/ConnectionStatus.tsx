import { cn } from '@/lib/utils';
import { CheckCircle, AlertCircle, Clock } from 'lucide-react';

interface ConnectionStatusProps {
  status: 'connected' | 'error' | 'pending';
  message?: string;
}

export function ConnectionStatus({ status, message }: ConnectionStatusProps) {
  const statusConfig = {
    connected: {
      label: 'Connected',
      icon: CheckCircle,
      className: 'bg-green-500/20 text-green-500 border-green-500/30',
      iconClass: 'text-green-500',
    },
    error: {
      label: 'Error',
      icon: AlertCircle,
      className: 'bg-red-500/20 text-red-500 border-red-500/30',
      iconClass: 'text-red-500',
    },
    pending: {
      label: 'Pending',
      icon: Clock,
      className: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
      iconClass: 'text-yellow-500',
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50 border border-border">
      <div className="flex items-center gap-3">
        <Icon className={cn('h-5 w-5', config.iconClass)} />
        <div>
          <p className="text-sm font-medium text-foreground">Connection Status</p>
          {message && (
            <p className="text-xs text-muted-foreground mt-0.5">{message}</p>
          )}
        </div>
      </div>
      <span className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        config.className
      )}>
        {config.label}
      </span>
    </div>
  );
}
