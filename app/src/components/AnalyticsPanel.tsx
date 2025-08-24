import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, Target, Zap, Shield } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export function AnalyticsPanel() {
  const [timeRange, setTimeRange] = useState('24h');

  // Mock analytics data
  const detectionData = [
    { time: '00:00', alerts: 12, blocked: 34, latency: 2.1 },
    { time: '04:00', alerts: 8, blocked: 23, latency: 1.9 },
    { time: '08:00', alerts: 25, blocked: 67, latency: 2.3 },
    { time: '12:00', alerts: 41, blocked: 89, latency: 2.7 },
    { time: '16:00', alerts: 33, blocked: 78, latency: 2.2 },
    { time: '20:00', alerts: 19, blocked: 45, latency: 2.0 }
  ];

  const threatTypeData = [
    { name: 'RPC Floods', value: 45, color: '#ef4444' },
    { name: 'Malicious Peers', value: 28, color: '#f97316' },
    { name: 'Suspicious Programs', value: 18, color: '#eab308' },
    { name: 'Other', value: 9, color: '#6b7280' }
  ];

  const performanceData = [
    { metric: 'Time to Detect (TTD)', value: '3.2s', target: '<5s', status: 'good' },
    { metric: 'Time to Mitigate (TTM)', value: '18.7s', target: '<20s', status: 'good' },
    { metric: 'False Positive Rate', value: '2.3%', target: '<5%', status: 'good' },
    { metric: 'Network Uptime', value: '99.94%', target: '>99.9%', status: 'good' },
    { metric: 'Precision', value: '94.2%', target: '>90%', status: 'good' },
    { metric: 'Recall', value: '89.1%', target: '>85%', status: 'good' }
  ];

  const regionData = [
    { region: 'US East', alerts: 156, coverage: 94, reporters: 47 },
    { region: 'EU West', alerts: 98, coverage: 87, reporters: 32 },
    { region: 'AP Southeast', alerts: 74, coverage: 81, reporters: 28 },
    { region: 'US West', alerts: 67, coverage: 76, reporters: 23 }
  ];

  return (
    <div className="space-y-6">
      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Detection Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">94.2%</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+2.1%</span> from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3.2s</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">-0.3s</span> improvement
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Threats Blocked</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2,847</div>
            <p className="text-xs text-muted-foreground">
              Last 24 hours
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Analytics Tabs */}
      <Tabs defaultValue="detection" className="space-y-4">
        <TabsList>
          <TabsTrigger value="detection">Detection Trends</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="threats">Threat Analysis</TabsTrigger>
          <TabsTrigger value="network">Network Health</TabsTrigger>
        </TabsList>

        <TabsContent value="detection" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Alert & Mitigation Timeline</CardTitle>
              <CardDescription>
                Real-time detection and blocking activity over the last 24 hours
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={detectionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="alerts" 
                    stroke="#ef4444" 
                    strokeWidth={2}
                    name="Alerts Generated"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="blocked" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="Threats Blocked"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Average Response Latency</CardTitle>
              <CardDescription>
                Time from detection to mitigation action
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={detectionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`${value}s`, 'Latency']} />
                  <Area 
                    type="monotone" 
                    dataKey="latency" 
                    stroke="#3b82f6" 
                    fill="#3b82f6" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                Key performance indicators against target thresholds
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {performanceData.map((metric, i) => (
                  <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <h4 className="font-medium">{metric.metric}</h4>
                      <p className="text-sm text-muted-foreground">Target: {metric.target}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold">{metric.value}</span>
                      <Badge variant={metric.status === 'good' ? 'default' : 'destructive'}>
                        {metric.status === 'good' ? '✓' : '!'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Precision vs Recall</CardTitle>
                <CardDescription>
                  Model accuracy over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={detectionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[80, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="precision" stroke="#10b981" strokeWidth={2} />
                    <Line type="monotone" dataKey="recall" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Network Efficiency</CardTitle>
                <CardDescription>
                  Resource utilization and throughput
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>CPU Utilization</span>
                    <span>23%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{width: '23%'}} />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Memory Usage</span>
                    <span>67%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-yellow-500 h-2 rounded-full" style={{width: '67%'}} />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Network Bandwidth</span>
                    <span>34%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{width: '34%'}} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="threats" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Threat Distribution</CardTitle>
                <CardDescription>
                  Types of threats detected in the last 24 hours
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={threatTypeData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    >
                      {threatTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Threat Timeline</CardTitle>
                <CardDescription>
                  Attack patterns throughout the day
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={detectionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="alerts" fill="#ef4444" name="Alerts" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Top Attack Vectors</CardTitle>
              <CardDescription>
                Most common attack methods detected
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { method: 'getAccountInfo flood', count: 1247, severity: 'high' },
                  { method: 'getProgramAccounts spam', count: 892, severity: 'high' },
                  { method: 'Invalid transaction signatures', count: 634, severity: 'medium' },
                  { method: 'Suspicious peer connections', count: 456, severity: 'medium' },
                  { method: 'Program upgrade anomalies', count: 287, severity: 'low' }
                ].map((attack, i) => (
                  <div key={i} className="flex items-center justify-between p-3 border rounded">
                    <div className="flex items-center gap-3">
                      <Badge variant={attack.severity === 'high' ? 'destructive' : attack.severity === 'medium' ? 'secondary' : 'outline'}>
                        {attack.severity.toUpperCase()}
                      </Badge>
                      <span className="font-medium">{attack.method}</span>
                    </div>
                    <span className="text-sm text-muted-foreground">{attack.count} detected</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="network" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Regional Network Status</CardTitle>
              <CardDescription>
                Coverage and activity across different regions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={regionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="region" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="alerts" fill="#ef4444" name="Alerts" />
                  <Bar dataKey="reporters" fill="#10b981" name="Reporters" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Network Health Score</CardTitle>
                <CardDescription>
                  Overall system health and reliability
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-600 mb-2">97.3%</div>
                  <p className="text-sm text-muted-foreground">Overall Health Score</p>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Reporter Uptime</span>
                    <span className="text-green-600">99.2%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Detection Accuracy</span>
                    <span className="text-green-600">94.2%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Network Coverage</span>
                    <span className="text-green-600">87.1%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Response Speed</span>
                    <span className="text-green-600">96.8%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Alert Resolution</CardTitle>
                <CardDescription>
                  How quickly alerts are resolved
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { timeRange: '< 5 minutes', percentage: 72, count: 1847 },
                    { timeRange: '5-15 minutes', percentage: 19, count: 487 },
                    { timeRange: '15-60 minutes', percentage: 7, count: 179 },
                    { timeRange: '> 1 hour', percentage: 2, count: 51 }
                  ].map((resolution, i) => (
                    <div key={i} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{resolution.timeRange}</span>
                        <span className="text-muted-foreground">{resolution.count} alerts</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div 
                          className="bg-primary h-2 rounded-full" 
                          style={{width: `${resolution.percentage}%`}} 
                        />
                      </div>
                      <div className="text-xs text-muted-foreground">{resolution.percentage}%</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}