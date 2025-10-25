/**
 * Docker Management API for SentinelKarma
 * Control and monitor Docker services programmatically
 */

import { exec, execSync, spawn } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';

const execAsync = promisify(exec);

// Types
interface CommandResult {
  success: boolean;
  stdout?: string;
  stderr?: string;
  returncode?: number;
}

interface ServiceStatus {
  [key: string]: 'running' | 'stopped' | 'unknown';
}

interface HealthCheck {
  [service: string]: {
    status: string;
    api?: string;
    mqtt?: string;
    details?: any;
  };
}

interface DockerStats {
  docker?: string;
  log_server?: any;
  data?: {
    contract_data: number;
    malicious_logs: number;
    logs_normal: number;
  };
}

interface MonitorOptions {
  full?: boolean;
  verbose?: boolean;
  mute?: boolean;
}

interface OverburstOptions {
  methods?: string[];
  rate?: number;
  errorRate?: number;
  baselineLatency?: number;
  burstLatency?: number;
  seconds?: number;
  parallel?: boolean;
}

/**
 * Docker Manager API for SentinelKarma services
 */
export class DockerManagerAPI {
  private projectDir: string;
  private managerScript: string;
  private services: string[] = [
    'mosquitto',
    'agent',
    'generator',
    'saver',
    'log-server'
  ];

  constructor(projectDir: string = '/home/water/SentinelKarma') {
    this.projectDir = projectDir;
    this.managerScript = path.join(projectDir, 'manager.sh');
  }

  /**
   * Run shell command
   */
  private async runCommand(
    cmd: string[],
    cwd?: string
  ): Promise<CommandResult> {
    try {
      const cmdStr = cmd.join(' ');
      const { stdout, stderr } = await execAsync(cmdStr, {
        cwd: cwd || this.projectDir
      });
      return {
        success: true,
        stdout,
        stderr
      };
    } catch (error: any) {
      return {
        success: false,
        stdout: error.stdout,
        stderr: error.stderr,
        returncode: error.code
      };
    }
  }

  /**
   * Run manager.sh with flags
   */
  private async runManager(flags: string[]): Promise<CommandResult> {
    return this.runCommand(['bash', this.managerScript, ...flags]);
  }

  /**
   * Run docker compose command
   */
  private async runDockerCompose(args: string[]): Promise<CommandResult> {
    return this.runCommand(['docker', 'compose', ...args]);
  }

  /**
   * Check if all dependencies are installed
   */
  async checkDependencies(): Promise<{ allPresent: boolean; output: string }> {
    const result = await this.runManager(['--check']);
    return {
      allPresent: result.success,
      output: result.stdout || ''
    };
  }

  /**
   * Install required dependencies
   */
  async installDependencies(): Promise<boolean> {
    const result = await this.runManager(['--install']);
    return result.success;
  }

  /**
   * Setup Docker and build images
   */
  async setupDocker(): Promise<boolean> {
    const result = await this.runManager(['--docker']);
    return result.success;
  }

  /**
   * Start services
   */
  async startServices(services?: string[]): Promise<boolean> {
    let result: CommandResult;
    if (services) {
      result = await this.runDockerCompose(['up', '-d', ...services]);
    } else {
      result = await this.runDockerCompose(['up', '-d']);
    }
    return result.success;
  }

  /**
   * Stop services
   */
  async stopServices(services?: string[]): Promise<boolean> {
    let result: CommandResult;
    if (services) {
      result = await this.runDockerCompose(['stop', ...services]);
    } else {
      result = await this.runManager(['--stop']);
    }
    return result.success;
  }

  /**
   * Restart a service
   */
  async restartService(service: string): Promise<boolean> {
    const result = await this.runDockerCompose(['restart', service]);
    return result.success;
  }

  /**
   * Get service status
   */
  async getServiceStatus(service?: string): Promise<ServiceStatus> {
    const args = service ? ['ps', service] : ['ps'];
    const result = await this.runDockerCompose(args);
    
    const services: ServiceStatus = {};
    
    if (result.success && result.stdout) {
      const lines = result.stdout.split('\n');
      
      for (const line of lines.slice(1)) {
        if (line.trim()) {
          const parts = line.split(/\s+/);
          if (parts.length >= 3) {
            const name = parts[0];
            const status = line.includes('Up') ? 'running' : 'stopped';
            services[name] = status;
          }
        }
      }
    }
    
    return services;
  }

  /**
   * Get logs from a service
   */
  async getLogs(service: string, lines: number = 100): Promise<string> {
    const result = await this.runDockerCompose([
      'logs',
      '--tail',
      lines.toString(),
      service
    ]);
    return result.stdout || '';
  }

  /**
   * Start monitoring
   */
  async monitorStart(options: MonitorOptions = {}): Promise<CommandResult> {
    const flags = ['--monitor'];
    
    if (options.full) flags.push('--full');
    if (options.verbose) flags.push('--verbose');
    if (options.mute) flags.push('--mute');
    
    return this.runManager(flags);
  }

  /**
   * Start test mode
   */
  async testMode(): Promise<boolean> {
    const result = await this.runManager(['--test']);
    return result.success;
  }

  /**
   * Run overburst test
   */
  async overburst(options: OverburstOptions = {}): Promise<boolean> {
    const env = { ...process.env };
    
    if (options.methods) {
      env.OVER_METHODS = options.methods.join(' ');
    }
    if (options.rate) {
      env.OVER_RATE = options.rate.toString();
    }
    if (options.errorRate) {
      env.OVER_ERR = options.errorRate.toString();
    }
    if (options.baselineLatency) {
      env.OVER_BASE_LAT = options.baselineLatency.toString();
    }
    if (options.burstLatency) {
      env.OVER_BURST_LAT = options.burstLatency.toString();
    }
    if (options.seconds) {
      env.OVER_SECS = options.seconds.toString();
    }
    if (options.parallel !== undefined) {
      env.OVER_PARALLEL = options.parallel ? '1' : '0';
    }
    
    try {
      execSync(`bash ${this.managerScript} --overburst`, {
        cwd: this.projectDir,
        env
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Build Docker images
   */
  async buildImages(): Promise<boolean> {
    const result = await this.runDockerCompose(['build']);
    return result.success;
  }

  /**
   * Purge project containers and images
   */
  async purgeProject(): Promise<boolean> {
    const result = await this.runManager(['--docker-purge']);
    return result.success;
  }

  /**
   * Execute command in service container
   */
  async execCommand(service: string, command: string): Promise<CommandResult> {
    return this.runDockerCompose(['exec', '-T', service, 'sh', '-c', command]);
  }

  /**
   * Check health of all services
   */
  async healthCheck(): Promise<HealthCheck> {
    const health: HealthCheck = {};
    
    // Get service status
    const status = await this.getServiceStatus();
    
    for (const service of this.services) {
      health[service] = {
        status: status[`sentinelkarma-${service}-1`] || 'unknown'
      };
    }
    
    // Special health checks
    try {
      // Log server health
      const response = await fetch('http://localhost:9000/health');
      if (response.ok) {
        health['log-server'].api = 'healthy';
        health['log-server'].details = await response.json();
      } else {
        health['log-server'].api = 'unreachable';
      }
    } catch {
      health['log-server'].api = 'unreachable';
    }
    
    // Mosquitto health
    const mqttResult = await this.execCommand(
      'mosquitto',
      "mosquitto_sub -h localhost -t '$SYS/#' -C 1"
    );
    health['mosquitto'].mqtt = mqttResult.success ? 'healthy' : 'unhealthy';
    
    return health;
  }

  /**
   * Get statistics
   */
  async getStats(): Promise<DockerStats> {
    const stats: DockerStats = {};
    
    // Docker stats
    const dockerResult = await this.runDockerCompose(['stats', '--no-stream']);
    if (dockerResult.success) {
      stats.docker = dockerResult.stdout;
    }
    
    // Log server stats
    try {
      const response = await fetch('http://localhost:9000/stats');
      if (response.ok) {
        stats.log_server = await response.json();
      }
    } catch {
      // Ignore
    }
    
    // Data directory stats
    const dataDir = path.join(this.projectDir, 'data');
    if (fs.existsSync(dataDir)) {
      const countFiles = (dir: string, pattern: string): number => {
        const fullPath = path.join(dataDir, dir);
        if (!fs.existsSync(fullPath)) return 0;
        return fs.readdirSync(fullPath)
          .filter(f => f.endsWith(pattern))
          .length;
      };
      
      stats.data = {
        contract_data: countFiles('contract_data', '.log'),
        malicious_logs: countFiles('malicious_logs', '.jsonl'),
        logs_normal: countFiles('logs_normal', '.jsonl')
      };
    }
    
    return stats;
  }

  /**
   * Stream logs in real-time
   */
  streamLogs(service: string, callback: (data: string) => void): void {
    const child = spawn('docker', ['compose', 'logs', '-f', service], {
      cwd: this.projectDir
    });
    
    child.stdout.on('data', (data) => {
      callback(data.toString());
    });
    
    child.stderr.on('data', (data) => {
      callback(`[ERROR] ${data.toString()}`);
    });
  }

  /**
   * Wait for service to be healthy
   */
  async waitForService(
    service: string,
    healthCheckUrl?: string,
    timeout: number = 30
  ): Promise<boolean> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout * 1000) {
      const status = await this.getServiceStatus(service);
      const serviceName = `sentinelkarma-${service}-1`;
      
      if (status[serviceName] === 'running') {
        if (healthCheckUrl) {
          try {
            const response = await fetch(healthCheckUrl);
            if (response.ok) {
              return true;
            }
          } catch {
            // Continue waiting
          }
        } else {
          return true;
        }
      }
      
      // Wait 1 second before next check
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    return false;
  }
}

// Example usage
if (require.main === module) {
  (async () => {
    console.log('Docker Manager API Examples');
    console.log('='.repeat(60));
    
    // Initialize API
    const docker = new DockerManagerAPI();
    
    // Check dependencies
    console.log('\n1. Checking dependencies...');
    const deps = await docker.checkDependencies();
    console.log(`   Dependencies OK: ${deps.allPresent}`);
    
    // Get service status
    console.log('\n2. Service Status:');
    const status = await docker.getServiceStatus();
    for (const [service, state] of Object.entries(status)) {
      console.log(`   ${service}: ${state}`);
    }
    
    // Health check
    console.log('\n3. Health Check:');
    const health = await docker.healthCheck();
    for (const [service, info] of Object.entries(health)) {
      console.log(`   ${service}: ${info.status}`);
    }
    
    // Get stats
    console.log('\n4. Statistics:');
    const stats = await docker.getStats();
    if (stats.data) {
      console.log(`   Contract data files: ${stats.data.contract_data}`);
      console.log(`   Malicious logs: ${stats.data.malicious_logs}`);
      console.log(`   Normal logs: ${stats.data.logs_normal}`);
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('Quick Usage:');
    console.log(`
import { DockerManagerAPI } from './docker-api';

// Initialize
const docker = new DockerManagerAPI();

// Start services
await docker.startServices();

// Start monitoring (full mode)
await docker.monitorStart({ full: true });

// Get logs
const logs = await docker.getLogs('agent', 50);

// Restart a service
await docker.restartService('log-server');

// Check health
const health = await docker.healthCheck();
    `);
  })();
}