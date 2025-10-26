import { useState, useEffect } from 'react';
import { AlertTriangle, Shield, Users, Code, BarChart3, Download, Bell, Settings, Home, Coins } from 'lucide-react';
import { Sidebar, SidebarContent, SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarProvider } from './components/ui/sidebar';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { DashboardOverview } from './components/DashboardOverview';
import { NFTsPanel } from './components/NFTsPanel';
import { LiveAlertsPanel } from './components/LiveAlertsPanel';
import { FraudulentIPsPanel } from './components/FraudulentIPsPanel';
import { SystemInfoPanel } from './components/SystemInfoPanel';

export default function App() {
  const [activePanel, setActivePanel] = useState('dashboard');
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
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'nfts', label: 'Network NFTs', icon: Coins },
    { id: 'alerts', label: 'Live Alerts', icon: AlertTriangle },
    { id: 'fraudips', label: 'Fraudulent IPs', icon: Shield },
    { id: 'system', label: 'System Info', icon: Settings },
  ];

  const renderPanel = () => {
    switch (activePanel) {
      case 'dashboard': return <DashboardOverview />;
      case 'nfts': return <NFTsPanel />;
      case 'alerts': return <LiveAlertsPanel />;
      case 'fraudips': return <FraudulentIPsPanel />;
      case 'system': return <SystemInfoPanel />;
      default: return <DashboardOverview />;
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