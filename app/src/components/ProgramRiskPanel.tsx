import { useState, useEffect } from 'react';
import { Code, AlertTriangle, CheckCircle, Clock, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Progress } from './ui/progress';
import { ScrollArea } from './ui/scroll-area';

interface ProgramRisk {
  id: string;
  programId: string;
  type: 'NEW_DEPLOYMENT' | 'UPGRADE' | 'AUTHORITY_CHANGE';
  riskScore: number;
  riskLevel: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'SAFE';
  deployedAt: Date;
  upgradeAuthority?: string;
  reasons: string[];
  bytecodeHash: string;
  size: number;
  reports: number;
  analysisComplete: boolean;
}

export function ProgramRiskPanel() {
  const [programRisks, setProgramRisks] = useState<ProgramRisk[]>([]);

  useEffect(() => {
    const mockProgramRisks: ProgramRisk[] = [
      {
        id: '1',
        programId: '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
        type: 'NEW_DEPLOYMENT',
        riskScore: 0.87,
        riskLevel: 'HIGH',
        deployedAt: new Date(Date.now() - 1800000),
        upgradeAuthority: 'UpgradeAuth123...ABC',
        reasons: [
          'Contains suspicious syscalls',
          'High complexity score',
          'New developer account',
          'No audit information'
        ],
        bytecodeHash: 'sha256:abc123def456...',
        size: 245678,
        reports: 3,
        analysisComplete: true
      },
      {
        id: '2',
        programId: 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
        type: 'UPGRADE',
        riskScore: 0.23,
        riskLevel: 'LOW',
        deployedAt: new Date(Date.now() - 3600000),
        upgradeAuthority: 'Known-Authority-XYZ',
        reasons: [
          'Established program',
          'Known upgrade authority',
          'Minor version update'
        ],
        bytecodeHash: 'sha256:def789ghi012...',
        size: 123456,
        reports: 0,
        analysisComplete: true
      },
      {
        id: '3',
        programId: 'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr',
        type: 'AUTHORITY_CHANGE',
        riskScore: 0.64,
        riskLevel: 'MEDIUM',
        deployedAt: new Date(Date.now() - 7200000),
        upgradeAuthority: 'NewAuth456...DEF',
        reasons: [
          'Authority transferred to unknown entity',
          'Previous authority had good reputation',
          'No verification of new authority'
        ],
        bytecodeHash: 'sha256:ghi345jkl678...',
        size: 89012,
        reports: 1,
        analysisComplete: false
      }
    ];

    setProgramRisks(mockProgramRisks);
  }, []);

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'destructive';
      case 'HIGH': return 'destructive';
      case 'MEDIUM': return 'secondary';
      case 'LOW': return 'outline';
      case 'SAFE': return 'outline';
      default: return 'outline';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'NEW_DEPLOYMENT': return 'default';
      case 'UPGRADE': return 'secondary';
      case 'AUTHORITY_CHANGE': return 'outline';
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Programs Monitored</CardTitle>
            <Code className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{programRisks.length}</div>
            <p className="text-xs text-muted-foreground">
              Last 24 hours
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Risk</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {programRisks.filter(p => p.riskLevel === 'HIGH' || p.riskLevel === 'CRITICAL').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Requires review
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">New Deployments</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {programRisks.filter(p => p.type === 'NEW_DEPLOYMENT').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Analysis Speed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12.3s</div>
            <p className="text-xs text-muted-foreground">
              Avg analysis time
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Program Risk Table */}
      <Card>
        <CardHeader>
          <CardTitle>Program Risk Assessment</CardTitle>
          <CardDescription>
            Monitoring new deployments, upgrades, and authority changes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Program ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Risk Level</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Deployed</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {programRisks.map((program) => (
                  <TableRow key={program.id}>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {program.programId.substring(0, 8)}...{program.programId.substring(-8)}
                      </code>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getTypeColor(program.type) as any} className="text-xs">
                        {program.type.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRiskColor(program.riskLevel) as any}>
                        {program.riskLevel}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <span className={`text-sm ${program.riskScore >= 0.8 ? 'text-destructive' : program.riskScore >= 0.6 ? 'text-yellow-600' : 'text-green-600'}`}>
                          {Math.round(program.riskScore * 100)}%
                        </span>
                        <Progress 
                          value={program.riskScore * 100} 
                          className="h-1"
                        />
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {Math.floor((Date.now() - program.deployedAt.getTime()) / 60000)}m ago
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {Math.round(program.size / 1024)}KB
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {program.analysisComplete ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <Clock className="w-4 h-4 text-yellow-500" />
                        )}
                        <span className="text-xs">
                          {program.analysisComplete ? 'Complete' : 'Analyzing'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button variant="outline" size="sm">
                        Analyze
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Risk Analysis Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Risk Factors</CardTitle>
            <CardDescription>
              Common patterns detected in program analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-4">
                {programRisks.map((program) => (
                  <div key={program.id} className="border rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {program.programId.substring(0, 8)}...
                      </code>
                      <Badge variant={getRiskColor(program.riskLevel) as any}>
                        {program.riskLevel}
                      </Badge>
                    </div>
                    <ul className="text-sm space-y-1">
                      {program.reasons.map((reason, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className={`w-1.5 h-1.5 rounded-full mt-1.5 ${
                            program.riskLevel === 'HIGH' || program.riskLevel === 'CRITICAL' 
                              ? 'bg-destructive' 
                              : program.riskLevel === 'MEDIUM' 
                                ? 'bg-yellow-500' 
                                : 'bg-green-500'
                          }`} />
                          <span className="text-muted-foreground">{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Analysis Pipeline</CardTitle>
            <CardDescription>
              Static and ML-based risk detection stages
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { stage: 'Bytecode Extraction', status: 'complete', time: '0.5s' },
                { stage: 'Static Rules Check', status: 'complete', time: '1.2s' },
                { stage: 'Syscall Analysis', status: 'complete', time: '2.1s' },
                { stage: 'ML Risk Classifier', status: 'complete', time: '8.5s' },
                { stage: 'Authority Verification', status: 'processing', time: '...' },
                { stage: 'Final Risk Score', status: 'pending', time: '...' }
              ].map((step, i) => (
                <div key={i} className="flex items-center justify-between p-3 border rounded">
                  <div className="flex items-center gap-3">
                    {step.status === 'complete' ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : step.status === 'processing' ? (
                      <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Clock className="w-4 h-4 text-muted-foreground" />
                    )}
                    <span className="text-sm">{step.stage}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">{step.time}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}