import { useState } from 'react';
import { Download, FileText, Settings, Shield, Code, Copy, Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner@2.0.3';

export function ExportPanel() {
  const [copied, setCopied] = useState(false);
  const [exportFormat, setExportFormat] = useState('yaml');
  const [includeReputations, setIncludeReputations] = useState(true);
  const [minRiskScore, setMinRiskScore] = useState('0.8');

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    toast('Copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast(`Downloaded ${filename}`);
  };

  const yamlBlocklist = `# SentinelKarma Network Defense Blocklist
# Generated: ${new Date().toISOString()}
# Format: YAML
# Minimum Risk Score: ${minRiskScore}

version: "1.0"
metadata:
  generator: "SentinelKarma v0.9"
  timestamp: "${new Date().toISOString()}"
  total_entries: 247
  min_risk_score: ${minRiskScore}

malicious_peers:
  - ip_hash: "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    asn_hash: "sha256:b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678"
    risk_score: 0.95
    category: "MALICIOUS"
    first_seen: "2025-08-15T10:30:00Z"
    reports: 23
    
  - ip_hash: "sha256:c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456789a"
    asn_hash: "sha256:d4e5f6789012345678901234567890abcdef1234567890abcdef123456789ab2"
    risk_score: 0.87
    category: "SUSPICIOUS"
    first_seen: "2025-08-17T14:20:00Z"
    reports: 12

suspicious_programs:
  - program_id: "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
    risk_score: 0.87
    category: "HIGH_RISK"
    deployed_at: "2025-08-19T16:45:00Z"
    reasons:
      - "Contains suspicious syscalls"
      - "High complexity score"
      - "New developer account"
      
rpc_patterns:
  flood_thresholds:
    getAccountInfo: 1000  # requests per minute
    getProgramAccounts: 100
    getTransaction: 2000
  
  rate_limits:
    per_ip_per_minute: 5000
    per_asn_per_minute: 50000`;

  const jsonBlocklist = `{
  "version": "1.0",
  "metadata": {
    "generator": "SentinelKarma v0.9",
    "timestamp": "${new Date().toISOString()}",
    "total_entries": 247,
    "min_risk_score": ${minRiskScore}
  },
  "malicious_peers": [
    {
      "ip_hash": "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
      "asn_hash": "sha256:b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678",
      "risk_score": 0.95,
      "category": "MALICIOUS",
      "first_seen": "2025-08-15T10:30:00Z",
      "reports": 23
    }
  ],
  "suspicious_programs": [
    {
      "program_id": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
      "risk_score": 0.87,
      "category": "HIGH_RISK",
      "deployed_at": "2025-08-19T16:45:00Z",
      "reasons": ["Contains suspicious syscalls", "High complexity score"]
    }
  ]
}`;

  const csvBlocklist = `# SentinelKarma Blocklist CSV Export
# Generated: ${new Date().toISOString()}
Type,Identifier,Risk Score,Category,First Seen,Reports
peer,sha256:a1b2c3d4e5f6...,0.95,MALICIOUS,2025-08-15T10:30:00Z,23
peer,sha256:c3d4e5f6789012...,0.87,SUSPICIOUS,2025-08-17T14:20:00Z,12
program,9WzDXwBbmkg8ZT...,0.87,HIGH_RISK,2025-08-19T16:45:00Z,3`;

  const getExportContent = () => {
    switch (exportFormat) {
      case 'json': return jsonBlocklist;
      case 'csv': return csvBlocklist;
      default: return yamlBlocklist;
    }
  };

  const getExportFilename = () => {
    const timestamp = new Date().toISOString().split('T')[0];
    return `sentinelkarma-blocklist-${timestamp}.${exportFormat}`;
  };

  return (
    <div className="space-y-6">
      {/* Export Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Blocked IPs</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
            <p className="text-xs text-muted-foreground">
              Active blocklist entries
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risky Programs</CardTitle>
            <Code className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">89</div>
            <p className="text-xs text-muted-foreground">
              Flagged programs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Export Size</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2.3MB</div>
            <p className="text-xs text-muted-foreground">
              Compressed archive
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2m</div>
            <p className="text-xs text-muted-foreground">
              ago
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="export" className="space-y-4">
        <TabsList>
          <TabsTrigger value="export">Export Data</TabsTrigger>
          <TabsTrigger value="settings">Configuration</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
        </TabsList>

        <TabsContent value="export" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Export Blocklist</CardTitle>
              <CardDescription>
                Download threat intelligence data for integration with your security systems
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Export Configuration */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="format">Export Format</Label>
                  <Select value={exportFormat} onValueChange={setExportFormat}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="yaml">YAML</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="csv">CSV</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="risk-score">Min Risk Score</Label>
                  <Select value={minRiskScore} onValueChange={setMinRiskScore}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0.9">90% (Critical only)</SelectItem>
                      <SelectItem value="0.8">80% (High+)</SelectItem>
                      <SelectItem value="0.6">60% (Medium+)</SelectItem>
                      <SelectItem value="0.0">0% (All entries)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center space-x-2 pt-8">
                  <Switch 
                    id="include-reputations" 
                    checked={includeReputations}
                    onCheckedChange={setIncludeReputations}
                  />
                  <Label htmlFor="include-reputations">Include reputation scores</Label>
                </div>
              </div>

              {/* Quick Export Buttons */}
              <div className="flex gap-2">
                <Button onClick={() => handleDownload(getExportContent(), getExportFilename())}>
                  <Download className="w-4 h-4 mr-2" />
                  Download {exportFormat.toUpperCase()}
                </Button>
                <Button variant="outline" onClick={() => handleCopy(getExportContent())}>
                  {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                  Copy to Clipboard
                </Button>
              </div>

              {/* Preview */}
              <div className="space-y-2">
                <Label>Preview</Label>
                <Textarea 
                  value={getExportContent().substring(0, 1000) + (getExportContent().length > 1000 ? '\n\n# ... truncated for preview' : '')}
                  readOnly
                  className="h-64 font-mono text-xs"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Detection Settings</CardTitle>
              <CardDescription>
                Configure threat detection parameters and thresholds
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">RPC Flood Detection</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="rpc-threshold">Request threshold (req/min)</Label>
                      <div className="w-24">
                        <Select defaultValue="1000">
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="500">500</SelectItem>
                            <SelectItem value="1000">1000</SelectItem>
                            <SelectItem value="2000">2000</SelectItem>
                            <SelectItem value="5000">5000</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label>Enable EWMA detection</Label>
                      <Switch defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label>Enable Isolation Forest</Label>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">Program Risk Analysis</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>Analyze new deployments</Label>
                      <Switch defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label>Monitor upgrades</Label>
                      <Switch defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label>Track authority changes</Label>
                      <Switch defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label htmlFor="ml-threshold">ML risk threshold</Label>
                      <div className="w-24">
                        <Select defaultValue="0.7">
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="0.5">50%</SelectItem>
                            <SelectItem value="0.7">70%</SelectItem>
                            <SelectItem value="0.8">80%</SelectItem>
                            <SelectItem value="0.9">90%</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t">
                <h4 className="font-medium mb-3">KARMA Token Settings</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label>Minimum stake requirement</Label>
                    <Badge variant="outline">1,000 KARMA</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label>False positive penalty</Label>
                    <Badge variant="outline">-5% stake</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label>Reward emission rate</Label>
                    <Badge variant="outline">0.15% daily</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label>Reputation decay</Label>
                    <Badge variant="outline">0.1% daily</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Integration Options</CardTitle>
              <CardDescription>
                Connect SentinelKarma with your existing security infrastructure
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">RPC Providers</CardTitle>
                    <CardDescription>
                      Integrate with Solana RPC endpoints
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Alchemy</span>
                      <Badge variant="outline">Available</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">QuickNode</span>
                      <Badge variant="outline">Available</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Helius</span>
                      <Badge variant="outline">Available</Badge>
                    </div>
                    <Button variant="outline" size="sm" className="w-full">
                      Configure RPC Integration
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Wallets</CardTitle>
                    <CardDescription>
                      Risk warnings in wallet interfaces
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Phantom</span>
                      <Badge variant="default">Integrated</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Solflare</span>
                      <Badge variant="secondary">Beta</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Backpack</span>
                      <Badge variant="outline">Planned</Badge>
                    </div>
                    <Button variant="outline" size="sm" className="w-full">
                      Request Integration
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Security Tools</CardTitle>
                    <CardDescription>
                      Export to existing security platforms
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">SIEM Systems</span>
                      <Badge variant="outline">JSON/CSV</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Threat Intel Platforms</span>
                      <Badge variant="outline">STIX/TAXII</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Firewall Rules</span>
                      <Badge variant="outline">IPTables</Badge>
                    </div>
                    <Button variant="outline" size="sm" className="w-full">
                      View Documentation
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">API Access</CardTitle>
                    <CardDescription>
                      Real-time threat intelligence feeds
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">REST API</span>
                      <Badge variant="default">v1.0</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">WebSocket Feed</span>
                      <Badge variant="default">Real-time</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">GraphQL</span>
                      <Badge variant="secondary">Beta</Badge>
                    </div>
                    <Button variant="outline" size="sm" className="w-full">
                      Get API Key
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}