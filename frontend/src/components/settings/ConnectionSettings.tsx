import { useState } from 'react';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ConnectionConfig {
  instanceType: 'cloud' | 'server';
  url: string;
  token: string;
}

interface ConnectionSettingsProps {
  source: 'jira' | 'confluence';
  config: ConnectionConfig;
  onUpdate: (config: ConnectionConfig) => void;
  onTestConnection: () => Promise<{ success: boolean; message: string }>;
}

export function ConnectionSettings({
  source,
  config,
  onUpdate,
  onTestConnection,
}: ConnectionSettingsProps) {
  const [showToken, setShowToken] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await onTestConnection();
      setTestResult(result);
    } catch {
      setTestResult({ success: false, message: 'Connection test failed' });
    } finally {
      setIsTesting(false);
    }
  };

  const sourceLabel = source === 'jira' ? 'Jira' : 'Confluence';

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-medium text-foreground">
          {sourceLabel} Connection Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Instance Type */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Instance Type</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name={`${source}-instance`}
                checked={config.instanceType === 'cloud'}
                onChange={() => onUpdate({ ...config, instanceType: 'cloud' })}
                className="w-4 h-4 text-primary"
              />
              <span className="text-sm text-foreground">Cloud</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name={`${source}-instance`}
                checked={config.instanceType === 'server'}
                onChange={() => onUpdate({ ...config, instanceType: 'server' })}
                className="w-4 h-4 text-primary"
              />
              <span className="text-sm text-foreground">Server / Data Center</span>
            </label>
          </div>
        </div>

        {/* URL */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            {sourceLabel} URL
          </label>
          <Input
            type="url"
            placeholder={`https://your-domain.atlassian.net`}
            value={config.url}
            onChange={(e) => onUpdate({ ...config, url: e.target.value })}
            className="bg-background"
          />
          <p className="text-xs text-muted-foreground">
            Enter your {sourceLabel} instance URL
          </p>
        </div>

        {/* Token */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Personal Access Token (PAT)
          </label>
          <div className="relative">
            <Input
              type={showToken ? 'text' : 'password'}
              placeholder="Enter your API token"
              value={config.token}
              onChange={(e) => onUpdate({ ...config, token: e.target.value })}
              className="bg-background pr-10"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
              onClick={() => setShowToken(!showToken)}
            >
              {showToken ? (
                <EyeOff className="h-4 w-4 text-muted-foreground" />
              ) : (
                <Eye className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Generate a token from your Atlassian account settings
          </p>
        </div>

        {/* Test Connection */}
        <div className="flex items-center gap-4 pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTestConnection}
            disabled={isTesting || !config.url || !config.token}
          >
            {isTesting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Test Connection
          </Button>
          {testResult && (
            <span className={cn(
              'text-sm',
              testResult.success ? 'text-green-500' : 'text-red-500'
            )}>
              {testResult.message}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
