import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Shield, Database, Coins, Activity, TrendingUp, Clock } from 'lucide-react';
import { dashboardAPI, nftAPI, type NFTMapping } from '../services/api';

export function DashboardOverview() {
  const [stats, setStats] = useState<any>(null);
  const [latestMints, setLatestMints] = useState<NFTMapping[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      console.log('[Dashboard] Loading data...');
      console.log('[Dashboard] Log Server URL:', 'http://localhost:9000');
      console.log('[Dashboard] Solana RPC URL:', 'http://localhost:8899');
      
      const [overview, mints] = await Promise.all([
        dashboardAPI.getOverview(),
        nftAPI.getLatestMints(5)
      ]);
      
      console.log('[Dashboard] Overview data:', overview);
      console.log('[Dashboard] Latest mints:', mints);
      
      setStats(overview);
      setLatestMints(mints);
    } catch (error) {
      console.error('[Dashboard] Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Log Server</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge variant={stats?.logServer?.healthy ? 'default' : 'destructive'}>
                {stats?.logServer?.healthy ? 'Online' : 'Offline'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {stats?.logServer?.logsStored || 0} logs stored
            </p>
            <p className="text-xs text-muted-foreground">
              {stats?.logServer?.storageUsedMb?.toFixed(2) || 0} / {stats?.logServer?.storageLimitMb || 1024} MB
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">NFTs Minted</CardTitle>
            <Coins className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.nfts?.totalMinted || 0}</div>
            <p className="text-xs text-muted-foreground">
              Total attack logs minted as NFTs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Solana Network</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge variant={stats?.solana?.healthy ? 'default' : 'destructive'}>
                {stats?.solana?.healthy ? 'Connected' : 'Disconnected'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Slot: {stats?.solana?.currentSlot || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Network Status</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">Active</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Auto-mint monitoring active
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Latest Mints */}
      <Card>
        <CardHeader>
          <CardTitle>Latest NFT Mints</CardTitle>
          <CardDescription>Recently minted attack log NFTs</CardDescription>
        </CardHeader>
        <CardContent>
          {latestMints.length === 0 ? (
            <p className="text-sm text-muted-foreground">No NFTs minted yet</p>
          ) : (
            <div className="space-y-4">
              {latestMints.map((mint, idx) => (
                <div key={idx} className="flex items-center justify-between border-b pb-3 last:border-0">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">{mint.filename}</p>
                    <p className="text-xs text-muted-foreground">
                      Hash: {mint.hash.substring(0, 16)}...
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {new Date(mint.timestamp * 1000).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant="outline" className="mb-1">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      Minted
                    </Badge>
                    <p className="text-xs text-muted-foreground">
                      <a 
                        href={mint.log_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="hover:underline"
                      >
                        View Log
                      </a>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* System Info */}
      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <CardDescription>Current system settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Check Interval:</span>
            <span className="font-medium">30 seconds</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">File Age Threshold:</span>
            <span className="font-medium">60 minutes</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Burst Protection:</span>
            <span className="font-medium">Disabled</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Log Rotation:</span>
            <span className="font-medium">30 seconds</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
