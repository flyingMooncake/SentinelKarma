/**
 * SentinelKarma TypeScript API Library
 * Complete API for log server and Solana contract interactions
 */

import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { exec, execSync } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// Types
interface UploadResponse {
  log_id: string;
  url: string;
  hash: string;
  size: number;
}

interface LogMetadata {
  log_id: string;
  filename: string;
  uploader: string;
  timestamp: number;
  hash: string;
  size: number;
}

interface HealthResponse {
  status: string;
  logs_stored: number;
  storage_used_mb: number;
  storage_limit_mb: number;
  authorized_peers: number;
  my_url: string;
}

interface StatsResponse {
  total_logs: number;
  total_size_bytes: number;
  total_size_mb: number;
  storage_limit_mb: number;
  authorized_peers: number;
  bandwidth_usage: Record<string, number>;
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

/**
 * Utility functions
 */
class Utils {
  /**
   * Get WSL IP address
   */
  static getWSLIP(): string {
    try {
      const result = execSync('hostname -I').toString().trim();
      return result.split(' ')[0];
    } catch {
      return '172.19.12.161'; // Fallback
    }
  }

  /**
   * Compute SHA256 hash of file
   */
  static computeFileHash(filepath: string): string {
    const fileBuffer = fs.readFileSync(filepath);
    const hashSum = crypto.createHash('sha256');
    hashSum.update(fileBuffer);
    return hashSum.digest('hex');
  }

  /**
   * Get public key from keypair file
   */
  static async getPubkeyFromKeypair(keypairPath: string): Promise<string> {
    try {
      const { stdout } = await execAsync(`solana-keygen pubkey ${keypairPath}`);
      return stdout.trim();
    } catch {
      return 'FKYCbhJfA4K5rVqFdunr55LXT6Qo5kbG5uxEPGkW1iCc';
    }
  }

  /**
   * Check if file is recent (modified within N minutes)
   */
  static isFileRecent(filepath: string, minutes: number = 10): boolean {
    const stats = fs.statSync(filepath);
    const now = Date.now();
    const fileTime = stats.mtimeMs;
    const cutoff = now - (minutes * 60 * 1000);
    return fileTime > cutoff;
  }
}

/**
 * HTTP Log Server API Client
 */
export class LogServerAPI {
  public serverUrl: string;
  public pubkey: string;
  private keypairPath?: string;

  constructor(
    serverUrl?: string,
    pubkey?: string,
    keypairPath?: string
  ) {
    // Auto-detect IP if not provided
    if (!serverUrl) {
      const ip = Utils.getWSLIP();
      serverUrl = `http://${ip}:9000`;
    }
    
    this.serverUrl = serverUrl.replace(/\/$/, '');
    this.pubkey = pubkey || 'FKYCbhJfA4K5rVqFdunr55LXT6Qo5kbG5uxEPGkW1iCc';
    this.keypairPath = keypairPath;
    
    // Get pubkey from keypair if needed
    if (!pubkey && keypairPath) {
      Utils.getPubkeyFromKeypair(keypairPath).then(pk => {
        this.pubkey = pk;
      });
    }
  }

  /**
   * Check server health
   */
  async health(): Promise<HealthResponse | null> {
    try {
      const response = await fetch(`${this.serverUrl}/health`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Health check failed:', error);
      return null;
    }
  }

  /**
   * Get server statistics
   */
  async stats(): Promise<StatsResponse | null> {
    try {
      const response = await fetch(`${this.serverUrl}/stats`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Stats fetch failed:', error);
      return null;
    }
  }

  /**
   * Upload a log file
   */
  async uploadLog(filepath: string): Promise<UploadResponse | { error: string }> {
    if (!fs.existsSync(filepath)) {
      return { error: `File not found: ${filepath}` };
    }

    const filename = path.basename(filepath);
    const timestamp = Math.floor(Date.now() / 1000);
    const fileContent = fs.readFileSync(filepath);
    
    const formData = new FormData();
    const blob = new Blob([fileContent], { type: 'application/octet-stream' });
    formData.append('file', blob, filename);

    try {
      const response = await fetch(`${this.serverUrl}/logs`, {
        method: 'POST',
        headers: {
          'X-Peer-Pubkey': this.pubkey,
          'X-Timestamp': timestamp.toString(),
          'X-Signature': 'test_signature',
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      } else {
        return { error: `Upload failed: ${response.status} ${response.statusText}` };
      }
    } catch (error) {
      return { error: String(error) };
    }
  }

  /**
   * Download a log file
   */
  async downloadLog(logId: string, outputPath?: string): Promise<boolean> {
    const timestamp = Math.floor(Date.now() / 1000);

    try {
      const response = await fetch(`${this.serverUrl}/logs/${logId}`, {
        headers: {
          'X-Peer-Pubkey': this.pubkey,
          'X-Timestamp': timestamp.toString(),
          'X-Signature': 'test_signature',
        },
      });

      if (response.ok) {
        const buffer = await response.arrayBuffer();
        if (outputPath) {
          fs.writeFileSync(outputPath, Buffer.from(buffer));
        }
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  /**
   * Get log metadata
   */
  async getMetadata(logId: string): Promise<LogMetadata | null> {
    try {
      const response = await fetch(`${this.serverUrl}/logs/${logId}/metadata`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch {
      return null;
    }
  }

  /**
   * List all available logs
   */
  async listLogs(): Promise<LogMetadata[]> {
    // Known log IDs from previous uploads
    const knownIds = [
      'ed2336ded3a9213a',
      '76d2cac8a861f1b9',
      'e5fa5faa647ef4dc',
      '9c0847bcf2109be5',
      'e87c7c582c50b96a'
    ];

    const logs: LogMetadata[] = [];
    for (const logId of knownIds) {
      const metadata = await this.getMetadata(logId);
      if (metadata) {
        logs.push(metadata);
      }
    }
    return logs;
  }

  /**
   * Check if file exists on server
   */
  async checkExists(fileHash: string): Promise<boolean> {
    const logId = fileHash.substring(0, 16);
    const metadata = await this.getMetadata(logId);
    return metadata !== null;
  }
}

/**
 * Sentinel Solana Contract API Client
 */
export class SentinelContractAPI {
  public rpcUrl: string;
  public keypairPath: string;
  public programId: string;
  public pubkey: string = '';

  constructor(
    rpcUrl?: string,
    keypairPath?: string,
    programId?: string
  ) {
    // Auto-detect RPC
    if (!rpcUrl) {
      const ip = Utils.getWSLIP();
      rpcUrl = `http://${ip}:8899`;
    }

    this.rpcUrl = rpcUrl;
    this.keypairPath = keypairPath || './sentinel/deploy-keypair.json';
    this.programId = programId || 'Da3fi9D86CM262Xbu8nCwiJRNc6wEgSoKH1cw3p1MA8V';

    // Get pubkey
    this.initPubkey();
  }

  private async initPubkey() {
    this.pubkey = await Utils.getPubkeyFromKeypair(this.keypairPath);
  }

  /**
   * Run Solana CLI command
   */
  private async runSolanaCmd(args: string[]): Promise<{ success: boolean; output?: string; error?: string }> {
    try {
      const cmd = `solana ${args.join(' ')} --url ${this.rpcUrl}`;
      const { stdout, stderr } = await execAsync(cmd);
      return { success: true, output: stdout };
    } catch (error: any) {
      return { success: false, error: error.stderr || error.message };
    }
  }

  /**
   * Get SOL balance
   */
  async getBalance(address?: string): Promise<number> {
    address = address || this.pubkey;
    const result = await this.runSolanaCmd(['balance', address]);
    if (result.success && result.output) {
      try {
        return parseFloat(result.output.split(' ')[0]);
      } catch {
        return 0;
      }
    }
    return 0;
  }

  /**
   * Request airdrop (testnet only)
   */
  async airdrop(amount: number = 100, address?: string): Promise<boolean> {
    address = address || this.pubkey;
    const result = await this.runSolanaCmd(['airdrop', amount.toString(), address]);
    return result.success;
  }

  /**
   * Create NFT mint
   */
  async createNFTMint(): Promise<string | null> {
    const tempKeypair = `/tmp/mint-${Date.now()}.json`;

    try {
      // Generate mint keypair
      await execAsync(`solana-keygen new --no-bip39-passphrase --outfile ${tempKeypair} --force`);
      
      // Get mint pubkey
      const { stdout } = await execAsync(`solana-keygen pubkey ${tempKeypair}`);
      const mintPubkey = stdout.trim();

      // Create token mint
      await execAsync(`spl-token create-token --decimals 0 --url ${this.rpcUrl} ${tempKeypair}`);

      return mintPubkey;
    } catch (error) {
      console.error('Failed to create NFT mint:', error);
      return null;
    } finally {
      // Cleanup
      if (fs.existsSync(tempKeypair)) {
        fs.unlinkSync(tempKeypair);
      }
    }
  }

  /**
   * Mint NFT for log (placeholder)
   */
  async mintNFT(logUrl: string, fileHash: string, mintAddress?: string): Promise<any> {
    // Create mint if not provided
    if (!mintAddress) {
      mintAddress = await this.createNFTMint();
      if (!mintAddress) {
        return { error: 'Failed to create NFT mint' };
      }
    }

    // TODO: Implement actual Anchor transaction
    return {
      status: 'placeholder',
      mint: mintAddress,
      log_url: logUrl,
      file_hash: fileHash,
      message: 'On-chain minting not yet implemented'
    };
  }

  /**
   * Get peer information (placeholder)
   */
  async getPeerInfo(peerAddress?: string): Promise<any> {
    peerAddress = peerAddress || this.pubkey;
    
    // TODO: Implement actual contract query
    return {
      peer: peerAddress,
      reputation: 100,
      posts_count: 0,
      message: 'Contract queries not yet implemented'
    };
  }
}

/**
 * Combined SentinelKarma API
 */
export class SentinelKarmaAPI {
  public ip: string;
  public logServer: LogServerAPI;
  public contract: SentinelContractAPI;
  public keypairPath: string;

  constructor(keypairPath?: string) {
    // Auto-detect IP
    this.ip = Utils.getWSLIP();
    this.keypairPath = keypairPath || './sentinel/deploy-keypair.json';

    // Initialize sub-APIs
    this.logServer = new LogServerAPI(
      `http://${this.ip}:9000`,
      undefined,
      keypairPath
    );

    this.contract = new SentinelContractAPI(
      `http://${this.ip}:8899`,
      keypairPath
    );
  }

  /**
   * Process log file (upload + mint)
   */
  async processLogFile(filepath: string): Promise<ProcessResult> {
    const result: ProcessResult = {
      file: filepath,
      upload: { error: 'Not processed' },
      mint: null
    };

    // Upload to log server
    const uploadResult = await this.logServer.uploadLog(filepath);
    result.upload = uploadResult;

    if ('error' in uploadResult) {
      return result;
    }

    // Mint NFT
    const mintResult = await this.contract.mintNFT(
      uploadResult.url,
      uploadResult.hash
    );
    result.mint = mintResult;

    return result;
  }

  /**
   * Get complete system status
   */
  async status(): Promise<SystemStatus> {
    const [health, stats, balance] = await Promise.all([
      this.logServer.health(),
      this.logServer.stats(),
      this.contract.getBalance()
    ]);

    return {
      ip: this.ip,
      log_server: {
        url: this.logServer.serverUrl,
        health,
        stats
      },
      contract: {
        rpc: this.contract.rpcUrl,
        program_id: this.contract.programId,
        balance,
        pubkey: this.contract.pubkey
      }
    };
  }

  /**
   * Batch process multiple files
   */
  async batchProcess(directory: string): Promise<ProcessResult[]> {
    const results: ProcessResult[] = [];
    
    if (!fs.existsSync(directory)) {
      console.error(`Directory not found: ${directory}`);
      return results;
    }

    const files = fs.readdirSync(directory)
      .filter(f => f.endsWith('.log'))
      .map(f => path.join(directory, f));

    for (const file of files) {
      console.log(`Processing: ${path.basename(file)}`);
      
      // Check if already uploaded
      const fileHash = Utils.computeFileHash(file);
      const exists = await this.logServer.checkExists(fileHash);
      
      if (exists) {
        console.log('  ��� Already uploaded');
        results.push({
          file,
          upload: { error: 'Already exists' },
          mint: null
        });
      } else {
        const result = await this.processLogFile(file);
        results.push(result);
        
        if ('log_id' in result.upload) {
          console.log(`  ✓ Uploaded: ${result.upload.log_id}`);
        } else {
          console.log(`  ✗ Failed: ${result.upload.error}`);
        }
      }
    }

    return results;
  }
}

// Export utilities
export { Utils };

// Example usage
if (require.main === module) {
  (async () => {
    console.log('SentinelKarma TypeScript API Example');
    console.log('=' .repeat(60));

    // Initialize API
    const api = new SentinelKarmaAPI();

    // Get status
    const status = await api.status();
    console.log('\nSystem Status:');
    console.log(`  IP: ${status.ip}`);
    console.log(`  Log Server: ${status.log_server.url}`);
    console.log(`  RPC: ${status.contract.rpc}`);
    console.log(`  Balance: ${status.contract.balance} SOL`);

    // List logs
    const logs = await api.logServer.listLogs();
    console.log(`\nAvailable Logs: ${logs.length}`);
    for (const log of logs) {
      console.log(`  - ${log.log_id}: ${log.filename} (${log.size} bytes)`);
    }
  })();
}