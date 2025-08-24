import { useState, useEffect } from 'react';
import { AlertTriangle, Shield, Users, Code, BarChart3, Download, Bell, Settings } from 'lucide-react';
import { Sidebar, SidebarContent, SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarProvider } from './components/ui/sidebar';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { AlertsPanel } from './components/AlertsPanel';
import { PeerRiskPanel } from './components/PeerRiskPanel';
import { ProgramRiskPanel } from './components/ProgramRiskPanel';
import { ReportersPanel } from './components/ReportersPanel';
import { AnalyticsPanel } from './components/AnalyticsPanel';
import { ExportPanel } from './components/ExportPanel';

export default function App() {
  const [activePanel, setActivePanel] = useState('alerts');
  const [alertCount, setAlertCount] = useState(3);

  // Simulate real-time alert updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        setAlertCount(prev => prev + 1);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const menuItems = [
    { id: 'alerts', label: 'Live Alerts', icon: AlertTriangle, badge: alertCount },
    { id: 'peers', label: 'Peer Risk', icon: Shield },
    { id: 'programs', label: 'Program Risk', icon: Code },
    { id: 'reporters', label: 'Reporters', icon: Users },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'export', label: 'Export', icon: Download }
  ];

  const renderPanel = () => {
    switch (activePanel) {
      case 'alerts': return <AlertsPanel />;
      case 'peers': return <PeerRiskPanel />;
      case 'programs': return <ProgramRiskPanel />;
      case 'reporters': return <ReportersPanel />;
      case 'analytics': return <AnalyticsPanel />;
      case 'export': return <ExportPanel />;
      default: return <AlertsPanel />;
    }
  };

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full bg-background">
        <Sidebar className="border-r border-border">
          <SidebarHeader className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="font-semibold">SentinelKarma</h1>
                <p className="text-sm text-muted-foreground">Network Defense</p>
              </div>
            </div>
          </SidebarHeader>
          
          <SidebarContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.id}>
                  <SidebarMenuButton 
                    onClick={() => setActivePanel(item.id)}
                    isActive={activePanel === item.id}
                    className="w-full justify-start"
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.label}</span>
                    {item.badge && (
                      <Badge variant="destructive" className="ml-auto">
                        {item.badge}
                      </Badge>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarContent>
        </Sidebar>

        <main className="flex-1 flex flex-col overflow-hidden">
          <header className="border-b border-border p-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold capitalize">{activePanel.replace(/([A-Z])/g, ' $1')}</h2>
              <p className="text-sm text-muted-foreground">
                Real-time distributed network defense for Solana
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-muted-foreground">Network Active</span>
              </div>
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </header>

          <div className="flex-1 overflow-auto p-6">
            {renderPanel()}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}