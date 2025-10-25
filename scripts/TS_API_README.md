# SentinelKarma TypeScript APIs

Complete TypeScript API libraries for the SentinelKarma system with full type safety and auto-IP detection.

## Installation

```bash
cd scripts
npm install

# Or with yarn
yarn install
```

## Quick Start

```typescript
import { SentinelKarmaAPI } from './sentinel-api';

// Initialize (auto-detects WSL IP)
const api = new SentinelKarmaAPI();

// Get system status
const status = await api.status();
console.log(`IP: ${status.ip}`); // Uses 172.19.12.161, not localhost!

// Process a log file
const result = await api.processLogFile('data/contract_data/test.log');
```

## Available APIs

### 1. SentinelKarmaAPI (Combined)

Main API combining all functionality:

```typescript
import { SentinelKarmaAPI } from './sentinel-api';

const api = new SentinelKarmaAPI();

// System status
const status = await api.status();

// Process file (upload + mint)
const result = await api.processLogFile('path/to/file.log');

// Batch process directory
const results = await api.batchProcess('data/contract_data');
```

### 2. LogServerAPI

HTTP log server operations:

```typescript
import { LogServerAPI } from './sentinel-api';

const api = new LogServerAPI(); // Auto-detects IP

// Health check
const health = await api.health();

// Upload log
const result = await api.uploadLog('file.log');
console.log(`Log ID: ${result.log_id}`);
console.log(`URL: ${result.url}`);

// Download log
await api.downloadLog('ed2336ded3a9213a', 'output.log');

// Check if exists
const exists = await api.checkExists(fileHash);

// List all logs
const logs = await api.listLogs();
```

### 3. SentinelContractAPI

Solana contract interactions:

```typescript
import { SentinelContractAPI } from './sentinel-api';

const api = new SentinelContractAPI(); // Auto-detects RPC

// Get balance
const balance = await api.getBalance();

// Request airdrop
await api.airdrop(100);

// Create NFT mint
const mint = await api.createNFTMint();

// Mint NFT
const result = await api.mintNFT(logUrl, fileHash);
```

### 4. DockerManagerAPI

Docker service management:

```typescript
import { DockerManagerAPI } from './docker-api';

const docker = new DockerManagerAPI();

// Start services
await docker.startServices();

// Monitor (full mode)
await docker.monitorStart({ full: true });

// Get status
const status = await docker.getServiceStatus();

// Get logs
const logs = await docker.getLogs('agent', 100);

// Health check
const health = await docker.healthCheck();

// Stream logs
docker.streamLogs('agent', (data) => {
  console.log(data);
});
```

## Type Definitions

All APIs are fully typed:

```typescript
interface UploadResponse {
  log_id: string;
  url: string;
  hash: string;
  size: number;
}

interface SystemStatus {
  ip: string;
  log_server: {
    url: string;
    health: HealthResponse | null;
    stats: StatsResponse | null;
  };
  contract: {
    rpc: string;
    program_id: string;
    balance: number;
    pubkey: string;
  };
}

interface ProcessResult {
  file: string;
  upload: UploadResponse | { error: string };
  mint: any;
}
```

## Utility Functions

```typescript
import { Utils } from './sentinel-api';

// Get WSL IP
const ip = Utils.getWSLIP(); // Returns actual IP, not localhost

// Compute file hash
const hash = Utils.computeFileHash('file.log');

// Check if file is recent
const isRecent = Utils.isFileRecent('file.log', 10); // < 10 minutes

// Get pubkey from keypair
const pubkey = await Utils.getPubkeyFromKeypair('keypair.json');
```

## Running Examples

```bash
# Run all examples
npm run example

# Or with ts-node
npx ts-node example-usage.ts

# Test individual APIs
npx ts-node sentinel-api.ts
npx ts-node docker-api.ts
```

## Building

```bash
# Compile TypeScript
npm run build

# Output in dist/
```

## Real-time Monitoring Example

```typescript
import { SentinelKarmaAPI, Utils } from './sentinel-api';

const api = new SentinelKarmaAPI();
const processed = new Set<string>();

async function monitor() {
  const files = fs.readdirSync('data/contract_data')
    .filter(f => f.endsWith('.log'));

  for (const file of files) {
    if (!processed.has(file) && Utils.isFileRecent(file)) {
      const hash = Utils.computeFileHash(file);
      
      if (!await api.logServer.checkExists(hash)) {
        const result = await api.processLogFile(file);
        console.log(`Processed: ${file}`);
      }
      
      processed.add(file);
    }
  }
}

// Check every minute
setInterval(monitor, 60000);
```

## Docker Management Example

```typescript
import { DockerManagerAPI } from './docker-api';

const docker = new DockerManagerAPI();

// Complete workflow
async function setupAndMonitor() {
  // Check dependencies
  const deps = await docker.checkDependencies();
  if (!deps.allPresent) {
    await docker.installDependencies();
  }

  // Start services
  await docker.startServices();

  // Wait for log server
  await docker.waitForService('log-server', 
    'http://localhost:9000/health', 30);

  // Start full monitoring
  await docker.monitorStart({ 
    full: true,    // Auto-mint mode
    verbose: false, // Only attacks
    mute: false    // Show output
  });
}

setupAndMonitor();
```

## Advanced Features

### Stream Processing

```typescript
// Stream logs in real-time
docker.streamLogs('agent', (data) => {
  if (data.includes('ATTACK')) {
    console.log('Attack detected:', data);
  }
});
```

### Batch Operations

```typescript
// Process all files in directory
const results = await api.batchProcess('data/contract_data');

// Filter successful uploads
const successful = results.filter(r => 
  'log_id' in r.upload
);

console.log(`Success: ${successful.length}/${results.length}`);
```

### Health Monitoring

```typescript
// Monitor service health
async function healthMonitor() {
  const health = await docker.healthCheck();
  
  for (const [service, info] of Object.entries(health)) {
    if (info.status !== 'running') {
      console.warn(`Service ${service} is ${info.status}`);
      
      // Restart if needed
      await docker.restartService(service);
    }
  }
}

setInterval(healthMonitor, 30000);
```

## Environment Variables

```typescript
// Override defaults
process.env.LOG_SERVER_URL = 'http://192.168.1.100:9000';
process.env.RPC_URL = 'http://192.168.1.100:8899';
process.env.KEYPAIR_PATH = '/path/to/keypair.json';
```

## Error Handling

```typescript
try {
  const result = await api.processLogFile('file.log');
  
  if ('error' in result.upload) {
    console.error('Upload failed:', result.upload.error);
  } else {
    console.log('Success:', result.upload.log_id);
  }
} catch (error) {
  console.error('Unexpected error:', error);
}
```

## Testing

```bash
# Install dev dependencies
npm install --save-dev @types/node ts-node typescript

# Run tests
npm test

# Run specific example
npx ts-node -e "
  import { SentinelKarmaAPI } from './sentinel-api';
  const api = new SentinelKarmaAPI();
  api.status().then(console.log);
"
```

## Features

- ✅ **Auto IP Detection**: Automatically uses WSL IP instead of localhost
- ✅ **Full Type Safety**: Complete TypeScript definitions
- ✅ **Async/Await**: Modern promise-based API
- ✅ **Error Handling**: Proper error types and handling
- ✅ **Real-time Streaming**: Stream logs and monitor changes
- ✅ **Batch Operations**: Process multiple files efficiently
- ✅ **Docker Integration**: Full control over services
- ✅ **Utility Functions**: Hash, IP detection, file checks

## Notes

- All APIs auto-detect WSL IP (not localhost)
- Testing mode enabled (no signature verification)
- NFT minting is placeholder (needs contract deployment)
- Requires Node.js 16+ for fetch API
- Log server must be running (`./manager.sh --monitor`)

## License

MIT