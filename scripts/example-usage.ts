/**
 * Example usage of SentinelKarma TypeScript APIs
 */

import { SentinelKarmaAPI, LogServerAPI, SentinelContractAPI, Utils } from './sentinel-api';
import { DockerManagerAPI } from './docker-api';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Example: Using Log Server API
 */
async function exampleLogServer() {
  console.log('='.repeat(60));
  console.log('LOG SERVER API EXAMPLES');
  console.log('='.repeat(60));

  // Initialize API (auto-detects IP)
  const api = new LogServerAPI();
  console.log(`Server URL: ${api.serverUrl}`);

  // Check health
  const health = await api.health();
  console.log('\nHealth:', JSON.stringify(health, null, 2));

  // Get stats
  const stats = await api.stats();
  console.log('\nStats:', JSON.stringify(stats, null, 2));

  // List existing logs
  const logs = await api.listLogs();
  console.log(`\nFound ${logs.length} logs:`);
  for (const log of logs) {
    console.log(`  - ${log.log_id}: ${log.filename}`);
  }

  // Upload a test file (if exists)
  const testFile = 'data/contract_data/test.log';
  if (fs.existsSync(testFile)) {
    const result = await api.uploadLog(testFile);
    console.log('Upload result:', result);
  }
}

/**
 * Example: Using Contract API
 */
async function exampleContract() {
  console.log('\n' + '='.repeat(60));
  console.log('CONTRACT API EXAMPLES');
  console.log('='.repeat(60));

  // Initialize API
  const api = new SentinelContractAPI();
  console.log(`RPC URL: ${api.rpcUrl}`);
  console.log(`Program ID: ${api.programId}`);
  
  // Wait for pubkey to be initialized
  await new Promise(resolve => setTimeout(resolve, 1000));
  console.log(`Pubkey: ${api.pubkey}`);

  // Check balance
  const balance = await api.getBalance();
  console.log(`\nBalance: ${balance} SOL`);

  // Request airdrop if low balance
  if (balance < 1) {
    console.log('Requesting airdrop...');
    const success = await api.airdrop(10);
    console.log(success ? '✓ Airdrop successful' : '✗ Airdrop failed');
  }

  // Create NFT mint (example)
  // const mint = await api.createNFTMint();
  // console.log(`Created NFT mint: ${mint}`);
}

/**
 * Example: Using Combined API
 */
async function exampleCombined() {
  console.log('\n' + '='.repeat(60));
  console.log('COMBINED API EXAMPLE');
  console.log('='.repeat(60));

  // Initialize combined API
  const api = new SentinelKarmaAPI();

  // Get complete system status
  const status = await api.status();
  console.log('System Status:');
  console.log(`  IP: ${status.ip}`);
  console.log(`  Log Server: ${status.log_server.url}`);
  console.log(`  Contract RPC: ${status.contract.rpc}`);
  console.log(`  Balance: ${status.contract.balance} SOL`);

  // Process a log file (upload + mint)
  const testFile = 'data/contract_data/test.log';
  if (fs.existsSync(testFile)) {
    const result = await api.processLogFile(testFile);
    console.log('Processing result:', JSON.stringify(result, null, 2));
  }
}

/**
 * Example: Batch processing
 */
async function exampleBatchProcessing() {
  console.log('\n' + '='.repeat(60));
  console.log('BATCH PROCESSING EXAMPLE');
  console.log('='.repeat(60));

  const api = new SentinelKarmaAPI();
  const logDir = 'data/contract_data';

  if (fs.existsSync(logDir)) {
    const results = await api.batchProcess(logDir);
    console.log(`Processed ${results.length} files`);
    
    for (const result of results) {
      const filename = path.basename(result.file);
      if ('log_id' in result.upload) {
        console.log(`  ✓ ${filename}: ${result.upload.log_id}`);
      } else {
        console.log(`  ✗ ${filename}: ${result.upload.error}`);
      }
    }
  }
}

/**
 * Example: Docker Management
 */
async function exampleDocker() {
  console.log('\n' + '='.repeat(60));
  console.log('DOCKER MANAGEMENT EXAMPLE');
  console.log('='.repeat(60));

  const docker = new DockerManagerAPI();

  // Check dependencies
  console.log('\nChecking dependencies...');
  const deps = await docker.checkDependencies();
  console.log(`Dependencies OK: ${deps.allPresent}`);

  // Get service status
  console.log('\nService Status:');
  const status = await docker.getServiceStatus();
  for (const [service, state] of Object.entries(status)) {
    console.log(`  ${service}: ${state}`);
  }

  // Health check
  console.log('\nHealth Check:');
  const health = await docker.healthCheck();
  for (const [service, info] of Object.entries(health)) {
    console.log(`  ${service}: ${info.status}`);
  }

  // Get stats
  console.log('\nStatistics:');
  const stats = await docker.getStats();
  if (stats.data) {
    console.log(`  Contract data files: ${stats.data.contract_data}`);
    console.log(`  Malicious logs: ${stats.data.malicious_logs}`);
    console.log(`  Normal logs: ${stats.data.logs_normal}`);
  }
}

/**
 * Example: Real-time monitoring
 */
async function exampleMonitoring() {
  console.log('\n' + '='.repeat(60));
  console.log('REAL-TIME MONITORING EXAMPLE');
  console.log('='.repeat(60));

  const api = new SentinelKarmaAPI();
  const docker = new DockerManagerAPI();

  // Monitor for new files
  console.log('\nMonitoring for new files...');
  
  const processedFiles = new Set<string>();
  
  async function checkForNewFiles() {
    const logDir = 'data/contract_data';
    if (!fs.existsSync(logDir)) return;

    const files = fs.readdirSync(logDir)
      .filter(f => f.endsWith('.log'))
      .map(f => path.join(logDir, f));

    for (const file of files) {
      if (!processedFiles.has(file)) {
        // Check if file is recent (< 10 minutes)
        if (Utils.isFileRecent(file, 10)) {
          console.log(`\nNew file detected: ${path.basename(file)}`);
          
          // Check if already uploaded
          const fileHash = Utils.computeFileHash(file);
          const exists = await api.logServer.checkExists(fileHash);
          
          if (!exists) {
            console.log('  Uploading...');
            const result = await api.logServer.uploadLog(file);
            
            if ('log_id' in result) {
              console.log(`  ✓ Uploaded: ${result.log_id}`);
              console.log(`  URL: ${result.url}`);
            } else {
              console.log(`  ✗ Failed: ${result.error}`);
            }
          } else {
            console.log('  ✓ Already uploaded');
          }
        }
        
        processedFiles.add(file);
      }
    }
  }

  // Check every 10 seconds (for demo)
  console.log('Checking every 10 seconds... (Press Ctrl+C to stop)');
  const interval = setInterval(checkForNewFiles, 10000);
  
  // Initial check
  await checkForNewFiles();
  
  // Stop after 30 seconds for demo
  setTimeout(() => {
    clearInterval(interval);
    console.log('\nMonitoring stopped');
  }, 30000);
}

/**
 * Main function
 */
async function main() {
  console.log('SentinelKarma TypeScript API Examples');
  console.log('='.repeat(60));

  // Get WSL IP
  const ip = Utils.getWSLIP();
  console.log(`\nDetected IP: ${ip}`);
  console.log('(Using auto-detected IP instead of localhost)');

  try {
    // Run examples
    await exampleLogServer();
    await exampleContract();
    await exampleCombined();
    await exampleBatchProcessing();
    await exampleDocker();
    // await exampleMonitoring(); // Uncomment to test monitoring

    // Quick usage guide
    console.log('\n' + '='.repeat(60));
    console.log('QUICK USAGE:');
    console.log('='.repeat(60));
    console.log(`
import { SentinelKarmaAPI } from './sentinel-api';

// Initialize (auto-detects IP)
const api = new SentinelKarmaAPI();

// Upload a log
const result = await api.logServer.uploadLog('path/to/file.log');

// Check if file exists
const exists = await api.logServer.checkExists(fileHash);

// Get balance
const balance = await api.contract.getBalance();

// Process file (upload + mint)
const processed = await api.processLogFile('path/to/file.log');

// Batch process directory
const results = await api.batchProcess('data/contract_data');
    `);

  } catch (error) {
    console.error('Error:', error);
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

// Export for use in other modules
export {
  exampleLogServer,
  exampleContract,
  exampleCombined,
  exampleBatchProcessing,
  exampleDocker,
  exampleMonitoring
};