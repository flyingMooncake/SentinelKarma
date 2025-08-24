import { useState, useEffect } from 'react';
import { Users, Award, TrendingUp, MapPin, Coins } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Progress } from './ui/progress';
import { Avatar, AvatarFallback } from './ui/avatar';

interface Reporter {
  id: string;
  address: string;
  region: string;
  asn: string;
  reputation: number;
  karmaStaked: number;
  reportsSubmitted: number;
  accuracyRate: number;
  rewardsEarned: number;
  slashingEvents: number;
  joinedAt: Date;
  lastActivity: Date;
  status: 'ACTIVE' | 'INACTIVE' | 'SLASHED';
  tier: 'BRONZE' | 'SILVER' | 'GOLD' | 'DIAMOND';
}

export function ReportersPanel() {
  const [reporters, setReporters] = useState<Reporter[]>([]);

  useEffect(() => {
    const mockReporters: Reporter[] = [
      {
        id: '1',
        address: 'Rpt1ABC...XYZ123',
        region: 'us-east-1',
        asn: 'AS13414',
        reputation: 0.94,
        karmaStaked: 10000,
        reportsSubmitted: 1247,
        accuracyRate: 0.92,
        rewardsEarned: 2847,
        slashingEvents: 2,
        joinedAt: new Date(Date.now() - 86400000 * 45),
        lastActivity: new Date(Date.now() - 1800000),
        status: 'ACTIVE',
        tier: 'GOLD'
      },
      {
        id: '2',
        address: 'Rpt2DEF...ABC456',
        region: 'eu-west-2',
        asn: 'AS16509',
        reputation: 0.87,
        karmaStaked: 7500,
        reportsSubmitted: 892,
        accuracyRate: 0.89,
        rewardsEarned: 1634,
        slashingEvents: 0,
        joinedAt: new Date(Date.now() - 86400000 * 32),
        lastActivity: new Date(Date.now() - 900000),
        status: 'ACTIVE',
        tier: 'SILVER'
      },
      {
        id: '3',
        address: 'Rpt3GHI...DEF789',
        region: 'ap-southeast-1',
        asn: 'AS7922',
        reputation: 0.76,
        karmaStaked: 5000,
        reportsSubmitted: 543,
        accuracyRate: 0.81,
        rewardsEarned: 987,
        slashingEvents: 1,
        joinedAt: new Date(Date.now() - 86400000 * 18),
        lastActivity: new Date(Date.now() - 3600000),
        status: 'ACTIVE',
        tier: 'BRONZE'
      },
      {
        id: '4',
        address: 'Rpt4JKL...GHI012',
        region: 'us-west-2',
        asn: 'AS15169',
        reputation: 0.23,
        karmaStaked: 2000,
        reportsSubmitted: 234,
        accuracyRate: 0.45,
        rewardsEarned: 123,
        slashingEvents: 8,
        joinedAt: new Date(Date.now() - 86400000 * 12),
        lastActivity: new Date(Date.now() - 14400000),
        status: 'SLASHED',
        tier: 'BRONZE'
      }
    ];

    setReporters(mockReporters);
  }, []);

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'DIAMOND': return 'bg-blue-500';
      case 'GOLD': return 'bg-yellow-500';
      case 'SILVER': return 'bg-gray-400';
      case 'BRONZE': return 'bg-amber-600';
      default: return 'bg-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'default';
      case 'INACTIVE': return 'secondary';
      case 'SLASHED': return 'destructive';
      default: return 'outline';
    }
  };

  const totalKarmaStaked = reporters.reduce((sum, r) => sum + r.karmaStaked, 0);
  const avgAccuracy = reporters.reduce((sum, r) => sum + r.accuracyRate, 0) / reporters.length;

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Reporters</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {reporters.filter(r => r.status === 'ACTIVE').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Across 12 regions
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">KARMA Staked</CardTitle>
            <Coins className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalKarmaStaked.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Total network stake
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Accuracy</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(avgAccuracy * 100)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Network reliability
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports/Hour</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
            <p className="text-xs text-muted-foreground">
              Current rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Reporters Table */}
      <Card>
        <CardHeader>
          <CardTitle>Reporter Network</CardTitle>
          <CardDescription>
            KARMA-staked agents providing network security intelligence
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Reporter</TableHead>
                  <TableHead>Region</TableHead>
                  <TableHead>Reputation</TableHead>
                  <TableHead>KARMA Staked</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>Reports</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reporters.map((reporter) => (
                  <TableRow key={reporter.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className={`text-white ${getTierColor(reporter.tier)}`}>
                            {reporter.tier[0]}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <code className="text-xs bg-muted px-2 py-1 rounded">
                            {reporter.address}
                          </code>
                          <div className="flex items-center gap-1 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {reporter.tier}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-muted-foreground" />
                        <span className="text-sm">{reporter.region}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">{reporter.asn}</div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <span className="text-sm font-medium">
                          {Math.round(reporter.reputation * 100)}%
                        </span>
                        <Progress 
                          value={reporter.reputation * 100} 
                          className="h-1"
                        />
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="font-medium">{reporter.karmaStaked.toLocaleString()}</div>
                      <div className="text-xs text-muted-foreground">
                        Earned: {reporter.rewardsEarned.toLocaleString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {Math.round(reporter.accuracyRate * 100)}%
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {reporter.slashingEvents > 0 && (
                          <span className="text-destructive">
                            {reporter.slashingEvents} slashes
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      {reporter.reportsSubmitted.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusColor(reporter.status) as any}>
                        {reporter.status}
                      </Badge>
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

      {/* Network Coverage Map & KARMA Economics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Regional Coverage</CardTitle>
            <CardDescription>
              Active reporters by geographic region
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { region: 'us-east-1', reporters: 47, coverage: 0.94 },
                { region: 'eu-west-2', reporters: 32, coverage: 0.87 },
                { region: 'ap-southeast-1', reporters: 28, coverage: 0.81 },
                { region: 'us-west-2', reporters: 23, coverage: 0.76 },
                { region: 'eu-central-1', reporters: 19, coverage: 0.69 },
                { region: 'ap-northeast-1', reporters: 15, coverage: 0.63 }
              ].map((region) => (
                <div key={region.region} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{region.region}</span>
                    <span className="text-sm text-muted-foreground">
                      {region.reporters} reporters
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress value={region.coverage * 100} className="flex-1 h-2" />
                    <span className="text-xs text-muted-foreground min-w-[40px]">
                      {Math.round(region.coverage * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>KARMA Economics</CardTitle>
            <CardDescription>
              Token incentives and slashing mechanisms
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-muted rounded">
                  <div className="text-lg font-bold text-green-600">+2,847</div>
                  <div className="text-xs text-muted-foreground">Rewards Distributed</div>
                </div>
                <div className="text-center p-3 bg-muted rounded">
                  <div className="text-lg font-bold text-destructive">-523</div>
                  <div className="text-xs text-muted-foreground">Tokens Slashed</div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Minimum Stake</span>
                  <span className="font-medium">1,000 KARMA</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Reward Rate</span>
                  <span className="font-medium">0.15% daily</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>False Positive Penalty</span>
                  <span className="font-medium text-destructive">-5% stake</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Malicious Report Penalty</span>
                  <span className="font-medium text-destructive">-25% stake</span>
                </div>
              </div>

              <Button className="w-full" variant="outline">
                Become a Reporter
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}