// API service for SentinelKarma backend integration

// Use relative URLs to leverage nginx proxy
const LOG_SERVER_URL = '/api';
const SOLANA_RPC_URL = 'http://localhost:8899';

export interface LogMetadata {
  log_id: string;
  filename: string;
  uploader: string;
  timestamp: number;
  hash: string;
  size: number;
}

export interface ServerStats {
  total_logs: number;
  total_size_bytes: number;
  total_size_mb: number;
  storage_limit_mb: number;
  authorized_peers: number;
  bandwidth_usage: Record<string, number>;
}

export interface NFTMapping {
  filename: string;
  log_url: string;
  hash: string;
  nft_tx: string;
  timestamp: number;
}

export interface PeerState {
  user: string;
  active: boolean;
  karma: number;
}

// Log Server API
export const logServerAPI = {
  async getHealth() {
    console.log('[API] Fetching log server health from:', `${LOG_SERVER_URL}/health`);
    try {
      const response = await fetch(`${LOG_SERVER_URL}/health`);
      const data = await response.json();
      console.log('[API] Log server health response:', data);
      return data;
    } catch (error) {
      console.error('[API] Log server health error:', error);
      throw error;
    }
  },

  async getStats(): Promise<ServerStats> {
    const response = await fetch(`${LOG_SERVER_URL}/stats`);
    return response.json();
  },

  async getLogMetadata(logId: string): Promise<LogMetadata> {
    const response = await fetch(`${LOG_SERVER_URL}/logs/${logId}/metadata`);
    return response.json();
  },

  async downloadLog(logId: string, pubkey: string) {
    const headers = {
      'X-Peer-Pubkey': pubkey,
      'X-Timestamp': String(Math.floor(Date.now() / 1000)),
      'X-Signature': 'test'
    };
    const response = await fetch(`${LOG_SERVER_URL}/logs/${logId}`, { headers });
    return response.blob();
  }
};

// NFT Mappings API (from local file)
export const nftAPI = {
  async getMappings(): Promise<NFTMapping[]> {
    try {
      const response = await fetch('/nft_mappings.json');
      if (!response.ok) return [];
      return response.json();
    } catch {
      return [];
    }
  },

  async getLatestMints(limit: number = 10): Promise<NFTMapping[]> {
    const mappings = await this.getMappings();
    return mappings
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  },

  async getTotalMinted(): Promise<number> {
    const mappings = await this.getMappings();
    return mappings.length;
  }
};

// Solana RPC API
export const solanaAPI = {
  async getHealth() {
    const response = await fetch(SOLANA_RPC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getHealth'
      })
    });
    return response.json();
  },

  async getSlot() {
    const response = await fetch(SOLANA_RPC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getSlot'
      })
    });
    const data = await response.json();
    return data.result;
  },

  async getTransaction(signature: string) {
    const response = await fetch(SOLANA_RPC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getTransaction',
        params: [signature, { encoding: 'json' }]
      })
    });
    const data = await response.json();
    return data.result;
  },

  async getBalance(pubkey: string) {
    const response = await fetch(SOLANA_RPC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getBalance',
        params: [pubkey]
      })
    });
    const data = await response.json();
    return data.result?.value || 0;
  },

  async getTokenAccountBalance(tokenAccount: string) {
    const response = await fetch(SOLANA_RPC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getTokenAccountBalance',
        params: [tokenAccount]
      })
    });
    const data = await response.json();
    return data.result?.value || null;
  },

  async getAccountInfo(pubkey: string) {
    const response = await fetch(SOLANA_RPC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getAccountInfo',
        params: [pubkey, { encoding: 'base64' }]
      })
    });
    const data = await response.json();
    return data.result?.value || null;
  }
};

// Combined dashboard stats
export const dashboardAPI = {
  async getOverview() {
    const [health, stats, nftCount, slot] = await Promise.all([
      logServerAPI.getHealth().catch(() => null),
      logServerAPI.getStats().catch(() => null),
      nftAPI.getTotalMinted().catch(() => 0),
      solanaAPI.getSlot().catch(() => 0)
    ]);

    return {
      logServer: {
        healthy: health?.status === 'healthy',
        logsStored: stats?.total_logs || 0,
        storageUsedMb: stats?.total_size_mb || 0,
        storageLimitMb: stats?.storage_limit_mb || 1024
      },
      nfts: {
        totalMinted: nftCount,
        latestMints: await nftAPI.getLatestMints(5)
      },
      solana: {
        healthy: slot > 0,
        currentSlot: slot
      }
    };
  }
};

export default {
  logServer: logServerAPI,
  nft: nftAPI,
  solana: solanaAPI,
  dashboard: dashboardAPI
};
