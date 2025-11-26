import { AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface AlertBannerProps {
  type: 'error' | 'warning' | 'info';
  title: string;
  message: string;
  linkText?: string;
  linkHref?: string;
  onClose?: () => void;
  onLinkClick?: () => void;
}

export function AlertBanner({
  type,
  title,
  message,
  linkText,
  onClose,
  onLinkClick,
}: AlertBannerProps) {
  const styles = {
    error: {
      container: 'bg-red-500/10 border-red-500/30',
      icon: 'text-red-500',
      title: 'text-red-500',
    },
    warning: {
      container: 'bg-yellow-500/10 border-yellow-500/30',
      icon: 'text-yellow-500',
      title: 'text-yellow-500',
    },
    info: {
      container: 'bg-blue-500/10 border-blue-500/30',
      icon: 'text-blue-500',
      title: 'text-blue-500',
    },
  };

  const icons = {
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const Icon = icons[type];
  const style = styles[type];

  return (
    <div className={cn(
      'flex items-start gap-3 p-4 rounded-lg border',
      style.container
    )}>
      <Icon className={cn('h-5 w-5 mt-0.5 shrink-0', style.icon)} />
      <div className="flex-1 min-w-0">
        <h4 className={cn('font-medium', style.title)}>{title}</h4>
        <p className="text-sm text-muted-foreground mt-1">{message}</p>
        {linkText && (
          <Button
            variant="link"
            size="sm"
            className={cn('p-0 h-auto mt-2', style.title)}
            onClick={onLinkClick}
          >
            {linkText} →
          </Button>
        )}
      </div>
      {onClose && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 shrink-0"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
