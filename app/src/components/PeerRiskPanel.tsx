import { useState, useEffect } from 'react';
import { Shield, AlertCircle, MapPin, Clock, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Progress } from './ui/progress';

interface PeerRisk {
  id: string;
  ipHash: string;
  asnHash: string;
  region: string;
  riskScore: number;
  category: 'MALICIOUS' | 'SUSPICIOUS' | 'MONITORING';
  firstSeen: Date;
  lastActivity: Date;
  reports: number;
  blockedConnections: number;
  reputation: number;
}

export function PeerRiskPanel() {
  const [peerRisks, setPeerRisks] = useState<PeerRisk[]>([]);

  useEffect(() => {
    const mockPeerRisks: PeerRisk[] = [
      {
        id: '1',
        ipHash: 'sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
        asnHash: 'sha256:b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678',
        region: 'us-east-1',
        riskScore: 0.95,
        category: 'MALICIOUS',
        firstSeen: new Date(Date.now() - 86400000 * 5),
        lastActivity: new Date(Date.now() - 3600000),
        reports: 23,
        blockedConnections: 1847,
        reputation: 0.05
      },
      {
        id: '2',
        ipHash: 'sha256:c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456789a',
        asnHash: 'sha256:d4e5f6789012345678901234567890abcdef1234567890abcdef123456789ab2',
        region: 'eu-west-2',
        riskScore: 0.78,
        category: 'SUSPICIOUS',
        firstSeen: new Date(Date.now() - 86400000 * 2),
        lastActivity: new Date(Date.now() - 7200000),
        reports: 12,
        blockedConnections: 634,
        reputation: 0.22
      },
      {
        id: '3',
        ipHash: 'sha256:e5f6789012345678901234567890abcdef1234567890abcdef123456789abc34',
        asnHash: 'sha256:f6789012345678901234567890abcdef1234567890abcdef123456789abc345d',
        region: 'ap-southeast-1',
        riskScore: 0.62,
        category: 'MONITORING',
        firstSeen: new Date(Date.now() - 86400000),
        lastActivity: new Date(Date.now() - 1800000),
        reports: 7,
        blockedConnections: 245,
        reputation: 0.38
      }
    ];

    setPeerRisks(mockPeerRisks);
  }, []);

  const getRiskColor = (score: number) => {
    if (score >= 0.8) return 'destructive';
    if (score >= 0.6) return 'secondary';
    return 'outline';
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'MALICIOUS': return 'destructive';
      case 'SUSPICIOUS': return 'secondary';
      case 'MONITORING': return 'outline';
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monitored Peers</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{peerRisks.length}</div>
            <p className="text-xs text-muted-foreground">
              Across 12 regions
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {peerRisks.filter(p => p.riskScore >= 0.8).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Actively malicious
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Blocked Today</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2,726</div>
            <p className="text-xs text-muted-foreground">
              Connection attempts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Coverage</CardTitle>
            <MapPin className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">94.3%</div>
            <p className="text-xs text-muted-foreground">
              Network visibility
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Peer Risk Table */}
      <Card>
        <CardHeader>
          <CardTitle>Peer Risk Monitor</CardTitle>
          <CardDescription>
            Anonymized tracking of malicious and suspicious peers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>IP Hash</TableHead>
                  <TableHead>ASN Region</TableHead>
                  <TableHead>Risk Score</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Reports</TableHead>
                  <TableHead>Blocked</TableHead>
                  <TableHead>Last Activity</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {peerRisks.map((peer) => (
                  <TableRow key={peer.id}>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {peer.ipHash.substring(7, 20)}...
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {peer.region}
                        </Badge>
                        <code className="text-xs">
                          {peer.asnHash.substring(7, 15)}...
                        </code>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-sm ${peer.riskScore >= 0.8 ? 'text-destructive' : peer.riskScore >= 0.6 ? 'text-yellow-600' : 'text-muted-foreground'}`}>
                            {Math.round(peer.riskScore * 100)}%
                          </span>
                        </div>
                        <Progress 
                          value={peer.riskScore * 100} 
                          className="h-1"
                        />
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getCategoryColor(peer.category) as any}>
                        {peer.category}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">{peer.reports}</TableCell>
                    <TableCell className="text-center font-medium">
                      {peer.blockedConnections.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {Math.floor((Date.now() - peer.lastActivity.getTime()) / 3600000)}h ago
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button variant="outline" size="sm">
                        Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Peer Activity</CardTitle>
          <CardDescription>
            Latest detections and risk assessments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { time: '2 minutes ago', event: 'High-risk peer detected in eu-west-1', severity: 'high' },
              { time: '7 minutes ago', event: 'Suspicious connection pattern blocked', severity: 'medium' },
              { time: '12 minutes ago', event: 'Peer reputation updated based on reports', severity: 'low' },
              { time: '18 minutes ago', event: 'New ASN range added to monitoring', severity: 'low' }
            ].map((activity, i) => (
              <div key={i} className="flex items-start gap-3 p-3 border rounded-lg">
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  activity.severity === 'high' ? 'bg-destructive' : 
                  activity.severity === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                }`} />
                <div className="flex-1">
                  <p className="text-sm">{activity.event}</p>
                  <p className="text-xs text-muted-foreground">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}