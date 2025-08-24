import { useState, useEffect } from 'react';
import { AlertTriangle, Clock, MapPin, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';

interface Alert {
  id: string;
  type: 'RPC_FLOOD' | 'MALICIOUS_PEER' | 'SUSPICIOUS_PROGRAM';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  timestamp: Date;
  source: string;
  description: string;
  details: {
    method?: string;
    errorRate?: number;
    latency?: number;
    ipHash?: string;
    programId?: string;
    region?: string;
  };
  reporters: number;
  confidence: number;
}

export function AlertsPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  // Mock alert data
  useEffect(() => {
    const mockAlerts: Alert[] = [
      {
        id: '1',
        type: 'RPC_FLOOD',
        severity: 'CRITICAL',
        timestamp: new Date(Date.now() - 2000),
        source: 'RPC-US-EAST-1',
        description: 'getAccountInfo flood detected',
        details: {
          method: 'getAccountInfo',
          errorRate: 0.85,
          latency: 2400,
          region: 'us-east-1'
        },
        reporters: 12,
        confidence: 0.94
      },
      {
        id: '2',
        type: 'MALICIOUS_PEER',
        severity: 'HIGH',
        timestamp: new Date(Date.now() - 30000),
        source: 'VALIDATOR-EU-2',
        description: 'Suspicious peer behavior detected',
        details: {
          ipHash: 'sha256:a1b2c3...',
          region: 'eu-west-2'
        },
        reporters: 7,
        confidence: 0.87
      },
      {
        id: '3',
        type: 'SUSPICIOUS_PROGRAM',
        severity: 'MEDIUM',
        timestamp: new Date(Date.now() - 120000),
        source: 'PROGRAM-MONITOR',
        description: 'New program with risky patterns',
        details: {
          programId: '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
          region: 'global'
        },
        reporters: 5,
        confidence: 0.73
      }
    ];

    setAlerts(mockAlerts);

    // Simulate new alerts
    const interval = setInterval(() => {
      if (Math.random() > 0.8) {
        const newAlert: Alert = {
          id: Date.now().toString(),
          type: ['RPC_FLOOD', 'MALICIOUS_PEER', 'SUSPICIOUS_PROGRAM'][Math.floor(Math.random() * 3)] as any,
          severity: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'][Math.floor(Math.random() * 4)] as any,
          timestamp: new Date(),
          source: `AGENT-${Math.floor(Math.random() * 100)}`,
          description: 'Real-time threat detected',
          details: { region: 'us-west-1' },
          reporters: Math.floor(Math.random() * 20) + 1,
          confidence: Math.random() * 0.3 + 0.7
        };
        setAlerts(prev => [newAlert, ...prev].slice(0, 50));
      }
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'destructive';
      case 'HIGH': return 'destructive';
      case 'MEDIUM': return 'secondary';
      case 'LOW': return 'outline';
      default: return 'outline';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'RPC_FLOOD': return '🌊';
      case 'MALICIOUS_PEER': return '🚫';
      case 'SUSPICIOUS_PROGRAM': return '⚠️';
      default: return '🔍';
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.length}</div>
            <p className="text-xs text-muted-foreground">
              +2 from last hour
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {alerts.filter(a => a.severity === 'CRITICAL').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Requires immediate action
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3.2s</div>
            <p className="text-xs text-muted-foreground">
              Target: &lt;5s TTD
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Network Coverage</CardTitle>
            <MapPin className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">247</div>
            <p className="text-xs text-muted-foreground">
              Active reporters
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alert Feed */}
      <Card>
        <CardHeader>
          <CardTitle>Live Alert Feed</CardTitle>
          <CardDescription>
            Real-time security alerts from the distributed network
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-start space-x-4 p-4 border rounded-lg">
                  <div className="text-2xl">{getTypeIcon(alert.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant={getSeverityColor(alert.severity) as any}>
                        {alert.severity}
                      </Badge>
                      <Badge variant="outline">
                        {alert.type.replace('_', ' ')}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        {alert.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <h4 className="font-medium mb-1">{alert.description}</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      Source: {alert.source} • {alert.reporters} reporters • {Math.round(alert.confidence * 100)}% confidence
                    </p>
                    {alert.details && (
                      <div className="text-xs space-y-1">
                        {alert.details.method && (
                          <div>Method: <code className="bg-muted px-1 rounded">{alert.details.method}</code></div>
                        )}
                        {alert.details.errorRate && (
                          <div>Error Rate: <span className="text-destructive">{Math.round(alert.details.errorRate * 100)}%</span></div>
                        )}
                        {alert.details.latency && (
                          <div>Latency: <span className="text-destructive">{alert.details.latency}ms</span></div>
                        )}
                        {alert.details.ipHash && (
                          <div>IP Hash: <code className="bg-muted px-1 rounded">{alert.details.ipHash}</code></div>
                        )}
                        {alert.details.programId && (
                          <div>Program ID: <code className="bg-muted px-1 rounded">{alert.details.programId}</code></div>
                        )}
                      </div>
                    )}
                  </div>
                  <Button variant="outline" size="sm">
                    Investigate
                  </Button>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}