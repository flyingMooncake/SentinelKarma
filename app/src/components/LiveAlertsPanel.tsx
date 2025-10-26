import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { AlertTriangle, Clock, Shield, Eye } from 'lucide-react';
import { logServerAPI } from '../services/api';

interface Alert {
  log_id: string;
  filename: string;
  timestamp: number;
  size: number;
  uploader: string;
}

export function LiveAlertsPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [minutes, setMinutes] = useState(60);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [minutes]);

  const loadAlerts = async () => {
    try {
      console.log('[LiveAlerts] Loading alerts for last', minutes, 'minutes...');
      
      // Get recent logs from HTTP server
      const response = await fetch(`/api/recent_logs?minutes=${minutes}`);
      const data = await response.json();
      
      console.log('[LiveAlerts] Response:', data);
      
      if (data.logs && data.logs.length > 0) {
        // Convert to alerts
        const alertsList: Alert[] = data.logs.map((log: any) => ({
          log_id: log.log_id,
          filename: log.filename,
          timestamp: log.timestamp,
          size: log.size,
          uploader: log.uploader
        }));
        
        console.log('[LiveAlerts] Found', alertsList.length, 'alerts');
        setAlerts(alertsList);
      } else {
        console.log('[LiveAlerts] No alerts found');
        setAlerts([]);
      }
    } catch (error) {
      console.error('[LiveAlerts] Failed to load alerts:', error);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  const cutoffTime = Date.now() - (minutes * 60 * 1000);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Live Alerts</h3>
          <p className="text-sm text-muted-foreground">
            HTTP alerts from the last {minutes} minutes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">Minutes:</label>
          <Input
            type="number"
            min="1"
            max="60"
            value={minutes}
            onChange={(e) => setMinutes(parseInt(e.target.value) || 5)}
            className="w-20"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : alerts.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <Shield className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">
              No alerts in the last {minutes} minutes
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              System is running normally
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {alerts.map((alert, idx) => (
            <Card key={idx}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-base flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-destructive" />
                      {alert.filename}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2">
                      <Clock className="h-3 w-3" />
                      {new Date(alert.timestamp * 1000).toLocaleString()}
                    </CardDescription>
                  </div>
                  <Badge variant="destructive">Alert</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Log ID:</span>
                    <span className="font-mono">{alert.log_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Size:</span>
                    <span>{(alert.size / 1024).toFixed(2)} KB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Uploader:</span>
                    <span className="font-mono text-xs">{alert.uploader.substring(0, 16)}...</span>
                  </div>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={async () => {
                    try {
                      const response = await fetch(`/api/view_log/${alert.log_id}`);
                      const data = await response.json();
                      alert(JSON.stringify(data, null, 2));
                    } catch (error) {
                      alert('Failed to load log data: ' + error);
                    }
                  }}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View Log Data
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
