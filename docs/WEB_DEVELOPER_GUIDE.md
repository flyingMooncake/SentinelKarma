# 🚀 SentinelKarma Web Developer Guide

A complete guide for web developers to understand, extend, and customize the SentinelKarma security dashboard.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Adding New Features](#adding-new-features)
6. [Component Library](#component-library)
7. [API Integration](#api-integration)
8. [Real-time Data](#real-time-data)
9. [Styling Guide](#styling-guide)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Common Tasks](#common-tasks)

## 🏃 Quick Start

```bash
# 1. Start the web dashboard
./manager.sh --web

# 2. Start with demo data
./manager.sh --web --monitor-all

# 3. Development mode (hot reload)
cd app
npm install
npm run dev
```

**Dashboard URL**: http://localhost:3000  
**API Server**: http://localhost:9000

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Dashboard                       │
│                   (TypeScript + Vite)                    │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   nginx proxy   │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    ┌───▼────┐        ┌────▼────┐       ┌─────▼─────┐
    │  API   │        │  MQTT   │       │  Solana   │
    │ Server │        │ Broker  │       │    RPC    │
    └────────┘        └─────────┘       └───────────┘
```

### Tech Stack

- **Framework**: React 18.3 with TypeScript
- **Build Tool**: Vite 5.4
- **UI Library**: Radix UI + shadcn/ui
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **State**: React hooks (useState, useEffect)

## 💻 Development Setup

### Prerequisites

- Node.js 18+ (installed via `./manager.sh --install`)
- npm or yarn
- Docker (for production build)

### Local Development

```bash
# Navigate to app directory
cd app

# Install dependencies
npm install

# Start dev server (hot reload)
npm run dev

# Open http://localhost:5173
```

### Using Docker

```bash
# Build and run with Docker
./manager.sh --web

# Update after changes
./manager.sh --update
```

## 📁 Project Structure

```
app/
├── src/
│   ├── App.tsx                    # Main app with routing
│   ├── main.tsx                   # Entry point
│   ├── index.css                  # Global styles
│   └── components/
│       ├── AlertsPanel.tsx        # Live alerts feed
│       ├── PeerRiskPanel.tsx      # Peer monitoring
│       ├── ProgramRiskPanel.tsx   # Program analysis
│       ├── ReportersPanel.tsx     # Network status
│       ├── AnalyticsPanel.tsx     # Charts & metrics
│       ├── ExportPanel.tsx        # Data export
│       └── ui/                    # Reusable components
│           ├── button.tsx
│           ├── card.tsx
│           ├── dialog.tsx
│           └── ... (40+ components)
├── public/                        # Static assets
├── index.html                     # HTML template
├── package.json                   # Dependencies
├── vite.config.ts                # Vite config
├── tsconfig.json                 # TypeScript config
├── Dockerfile                    # Production build
└── nginx.conf                    # nginx config
```

## 🎨 Adding New Features

### 1. Create a New Panel

Create `src/components/CustomPanel.tsx`:

```typescript
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

export function CustomPanel() {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    // Fetch data from API
    fetchCustomData().then(setData);
  }, []);
  
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Custom Panel</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Your content here */}
        </CardContent>
      </Card>
    </div>
  );
}
```

### 2. Add to Navigation

Update `src/App.tsx`:

```typescript
// Add to menu items
const menuItems = [
  // ... existing items
  { id: 'custom', label: 'Custom Panel', icon: Star },
];

// Add to render switch
const renderPanel = () => {
  switch (activePanel) {
    // ... existing cases
    case 'custom': return <CustomPanel />;
  }
};
```

### 3. Connect to Real Data

Create `src/hooks/useCustomData.ts`:

```typescript
export function useCustomData() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:9000/api/custom');
        const json = await response.json();
        setData(json);
      } catch (error) {
        console.error('Failed to fetch:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    
    return () => clearInterval(interval);
  }, []);
  
  return { data, loading };
}
```

## 🧩 Component Library

### Available UI Components

All components are in `src/components/ui/`:

| Component | Usage | Example |
|-----------|-------|---------|
| Button | Interactive actions | `<Button variant="destructive">Delete</Button>` |
| Card | Content containers | `<Card><CardHeader>...</CardHeader></Card>` |
| Badge | Status indicators | `<Badge variant="success">Active</Badge>` |
| Dialog | Modal windows | `<Dialog><DialogContent>...</DialogContent></Dialog>` |
| Table | Data display | `<Table><TableBody>...</TableBody></Table>` |
| Tabs | Tabbed content | `<Tabs><TabsList>...</TabsList></Tabs>` |
| Alert | Notifications | `<Alert><AlertDescription>...</AlertDescription></Alert>` |
| Progress | Loading states | `<Progress value={75} />` |
| ScrollArea | Scrollable regions | `<ScrollArea className="h-96">...</ScrollArea>` |

### Using Components

```typescript
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

function MyComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
        <Badge>Status</Badge>
      </CardHeader>
      <CardContent>
        <Button onClick={() => alert('Clicked!')}>
          Click Me
        </Button>
      </CardContent>
    </Card>
  );
}
```

## 🔌 API Integration

### Connecting to Log Server

```typescript
// src/services/api.ts
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:9000';

export async function fetchLogs() {
  const response = await fetch(`${API_BASE}/logs`);
  return response.json();
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE}/health`);
  return response.json();
}

export async function fetchStats() {
  const response = await fetch(`${API_BASE}/stats`);
  return response.json();
}
```

### Using in Components

```typescript
import { useEffect, useState } from 'react';
import { fetchStats } from '@/services/api';

function StatsPanel() {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetchStats().then(setStats);
  }, []);
  
  if (!stats) return <div>Loading...</div>;
  
  return (
    <div>
      <p>Total Logs: {stats.total_logs}</p>
      <p>Storage Used: {stats.total_size_mb} MB</p>
    </div>
  );
}
```

## 📡 Real-time Data

### WebSocket Connection (Future)

```typescript
// src/hooks/useWebSocket.ts
export function useWebSocket(url: string) {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData(message);
    };
    ws.onclose = () => setIsConnected(false);
    
    return () => ws.close();
  }, [url]);
  
  return { data, isConnected };
}

// Usage
function LiveAlerts() {
  const { data, isConnected } = useWebSocket('ws://localhost:9001');
  
  return (
    <div>
      {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}
```

### Polling for Updates

```typescript
// src/hooks/usePolling.ts
export function usePolling(fetchFn: () => Promise<any>, interval = 5000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const poll = async () => {
      try {
        const result = await fetchFn();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err);
      }
    };
    
    poll(); // Initial fetch
    const timer = setInterval(poll, interval);
    
    return () => clearInterval(timer);
  }, [fetchFn, interval]);
  
  return { data, error };
}
```

## 🎨 Styling Guide

### Tailwind Classes

```typescript
// Common patterns
<div className="space-y-6">           {/* Vertical spacing */}
<div className="grid grid-cols-4 gap-4"> {/* Grid layout */}
<div className="flex items-center gap-2"> {/* Flexbox */}
<div className="p-4 border rounded-lg">   {/* Card style */}
```

### Color Scheme

```typescript
// Severity colors
const severityColors = {
  critical: 'destructive',  // Red
  high: 'destructive',      // Red
  medium: 'secondary',      // Yellow
  low: 'outline',          // Gray
};

// Usage
<Badge variant={severityColors[alert.severity]}>
  {alert.severity}
</Badge>
```

### Dark Mode Support

```css
/* index.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
  }
  
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
  }
}
```

## 🧪 Testing

### Unit Tests (Setup Required)

```bash
# Install testing dependencies
npm install --save-dev @testing-library/react vitest

# Create test file
# src/components/__tests__/AlertsPanel.test.tsx
```

```typescript
import { render, screen } from '@testing-library/react';
import { AlertsPanel } from '../AlertsPanel';

test('renders alerts panel', () => {
  render(<AlertsPanel />);
  expect(screen.getByText('Live Alert Feed')).toBeInTheDocument();
});
```

### Manual Testing

```bash
# 1. Start with mock data
./manager.sh --web --monitor-all

# 2. Test specific features
# - Click through all panels
# - Verify data updates
# - Check responsive design
# - Test error states
```

## 🚀 Deployment

### Production Build

```bash
# Using manager script
./manager.sh --update

# Or manually
cd app
npm run build
docker build -t sentinelkarma-web .
```

### Environment Variables

```bash
# .env.production
REACT_APP_API_URL=https://api.sentinelkarma.com
REACT_APP_WS_URL=wss://ws.sentinelkarma.com
```

## 📝 Common Tasks

### Add a New Chart

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function MetricsChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#8884d8" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### Add Loading States

```typescript
function DataPanel() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  
  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </CardContent>
      </Card>
    );
  }
  
  return <div>{/* Your content */}</div>;
}
```

### Add Error Handling

```typescript
function SafePanel() {
  const [error, setError] = useState(null);
  
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    );
  }
  
  return <div>{/* Your content */}</div>;
}
```

### Add Filtering

```typescript
function FilterableList() {
  const [filter, setFilter] = useState('');
  const [items, setItems] = useState([]);
  
  const filtered = items.filter(item => 
    item.name.toLowerCase().includes(filter.toLowerCase())
  );
  
  return (
    <>
      <Input
        placeholder="Filter..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />
      <div className="space-y-2">
        {filtered.map(item => (
          <div key={item.id}>{item.name}</div>
        ))}
      </div>
    </>
  );
}
```

## 🔧 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Port 3000 in use | Change port in `vite.config.ts` |
| API connection failed | Check if log-server is running: `docker ps` |
| Build fails | Clear cache: `rm -rf node_modules && npm install` |
| Hot reload not working | Check file watchers: `echo fs.inotify.max_user_watches=524288` |
| Docker build fails | Ensure Node.js 18+: `node --version` |

### Debug Mode

```typescript
// Enable debug logging
if (process.env.NODE_ENV === 'development') {
  console.log('Debug:', data);
}

// Add to component
useEffect(() => {
  console.log('Component mounted');
  return () => console.log('Component unmounted');
}, []);
```

## 📚 Resources

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Radix UI](https://www.radix-ui.com/docs)
- [shadcn/ui](https://ui.shadcn.com/docs)
- [Recharts](https://recharts.org/en-US/api)
- [Vite Guide](https://vitejs.dev/guide/)

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test thoroughly**: `npm run dev`
5. **Build for production**: `npm run build`
6. **Submit a pull request**

## 💡 Tips for Success

1. **Start Small**: Add one feature at a time
2. **Use TypeScript**: It catches errors early
3. **Follow Patterns**: Look at existing components
4. **Test Often**: Use dev server with hot reload
5. **Ask Questions**: The codebase is well-documented
6. **Keep It Simple**: Don't over-engineer
7. **Mobile First**: Design for mobile, enhance for desktop

## 🎯 Next Steps

1. **Explore the Code**: Start with `App.tsx`
2. **Run Dev Server**: `cd app && npm run dev`
3. **Modify a Panel**: Try changing `AlertsPanel.tsx`
4. **Add Your Feature**: Follow the guide above
5. **Test with Real Data**: Connect to actual API
6. **Deploy**: Use Docker for production

---

**Happy Coding! 🚀**

For questions or issues, check the main [README.md](../README.md) or open an issue on GitHub.