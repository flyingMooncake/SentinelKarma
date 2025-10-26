import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { CheckCircle2, XCircle, Coins, TrendingUp, Wallet, Send } from 'lucide-react';
import { solanaAPI } from '../services/api';

interface SystemInfo {
  isPeer: boolean;
  karma: number;
  solBalance: number;
  sekaBalance: number;
  walletAddress: string;
}

export function SystemInfoPanel() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [sendTo, setSendTo] = useState('');
  const [sendAmount, setSendAmount] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadSystemInfo();
    const interval = setInterval(loadSystemInfo, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const loadSystemInfo = async () => {
    try {
      // Use the wallet from auto-mint config
      const WALLET_ADDRESS = 'C3rYiwncXkDmFGrFMwBVxhe6vUw2YTphLq9JGdTjcmKH';
      const SEKA_MINT = '82UjXqRTyzNxkchsrwNmA7KgWgPFQ1QDDpUVo37ar6qE';
      
      console.log('[SystemInfo] Loading for wallet:', WALLET_ADDRESS);
      
      // Fetch SOL balance
      const solLamports = await solanaAPI.getBalance(WALLET_ADDRESS);
      const solBalance = solLamports / 1_000_000_000; // Convert lamports to SOL
      console.log('[SystemInfo] SOL balance:', solBalance);
      
      // Fetch SEKA balance by getting all token accounts
      let sekaBalance = 0;
      try {
        // Get token accounts for this wallet
        const response = await fetch('http://localhost:8899', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'getTokenAccountsByOwner',
            params: [
              WALLET_ADDRESS,
              { mint: SEKA_MINT },
              { encoding: 'jsonParsed' }
            ]
          })
        });
        
        const data = await response.json();
        console.log('[SystemInfo] Token accounts response:', data);
        
        if (data.result?.value?.length > 0) {
          const tokenAccount = data.result.value[0];
          const amount = tokenAccount.account.data.parsed.info.tokenAmount.uiAmount;
          sekaBalance = amount;
          console.log('[SystemInfo] SEKA balance:', sekaBalance);
        }
      } catch (e) {
        console.error('[SystemInfo] Could not fetch SEKA balance:', e);
      }
      
      // Check peer status and karma from Sentinel contract
      // For now, assume peer is active
      const isPeer = true;
      const karma = 0; // TODO: Fetch from contract
      
      setInfo({
        isPeer,
        karma,
        solBalance,
        sekaBalance,
        walletAddress: WALLET_ADDRESS
      });
    } catch (error) {
      console.error('[SystemInfo] Failed to load system info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinNetwork = async () => {
    setJoining(true);
    try {
      // Call join_network instruction
      alert('Join network functionality - integrate with Sentinel contract');
      await loadSystemInfo();
    } catch (error) {
      console.error('Failed to join network:', error);
      alert('Failed to join network: ' + error);
    } finally {
      setJoining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!info) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Failed to load system information
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">System Information</h3>
        <p className="text-sm text-muted-foreground">
          Your peer status and balances
        </p>
      </div>

      {/* Peer Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Network Peer Status</CardTitle>
            {info.isPeer ? (
              <Badge variant="default" className="bg-green-500">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Active Peer
              </Badge>
            ) : (
              <Badge variant="destructive">
                <XCircle className="h-3 w-3 mr-1" />
                Not a Peer
              </Badge>
            )}
          </div>
          <CardDescription>
            {info.isPeer 
              ? 'You are an active member of the Sentinel network'
              : 'Join the network to start earning karma'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!info.isPeer && (
            <Button 
              onClick={handleJoinNetwork} 
              disabled={joining}
              className="w-full"
            >
              {joining ? 'Joining...' : 'Join Network (1,000 SEKA)'}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Karma */}
      {info.isPeer && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Peer Karma
            </CardTitle>
            <CardDescription>
              Earned from quality attack log submissions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-primary">
              {info.karma.toLocaleString()}
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Refreshes every 10 seconds
            </p>
          </CardContent>
        </Card>
      )}

      {/* Wallet Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            Wallet
          </CardTitle>
          <CardDescription className="font-mono text-xs">
            {info.walletAddress}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                <Coins className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">SOL Balance</p>
                <p className="text-xs text-muted-foreground">Solana</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold">{info.solBalance.toFixed(4)}</p>
              <p className="text-xs text-muted-foreground">SOL</p>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-green-500/10 rounded-full flex items-center justify-center">
                <Coins className="h-4 w-4 text-green-500" />
              </div>
              <div>
                <p className="text-sm font-medium">SEKA Balance</p>
                <p className="text-xs text-muted-foreground">Sentinel Token</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold">{info.sekaBalance.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">SEKA</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Send SEKA - Disabled for demo (requires host spl-token access) */}
      {false && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Send className="h-5 w-5" />
              Send SEKA
            </CardTitle>
            <CardDescription>Transfer SEKA tokens to another wallet</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Recipient Address</label>
              <Input
                placeholder="Solana public key"
                value={sendTo}
                onChange={(e) => setSendTo(e.target.value)}
                className="font-mono text-xs"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Amount (SEKA)</label>
              <Input
                type="number"
                placeholder="0.00"
                value={sendAmount}
                onChange={(e) => setSendAmount(e.target.value)}
              />
            </div>
            <Button 
              onClick={async () => {
                setSending(true);
                try {
                  console.log('[SendSEKA] Sending', sendAmount, 'SEKA to', sendTo);
                  
                  const response = await fetch('/api/transfer_seka', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      recipient: sendTo,
                      amount: parseFloat(sendAmount)
                    })
                  });
                  
                  const data = await response.json();
                  console.log('[SendSEKA] Response:', data);
                  
                  if (response.ok && data.success) {
                    alert(`✅ Success!\n\nSent ${data.amount} SEKA to ${data.recipient}\n\nSignature: ${data.signature}`);
                    setSendTo('');
                    setSendAmount('');
                    await loadSystemInfo(); // Refresh balances
                  } else {
                    const errorMsg = data.detail || data.error || 'Transfer failed';
                    throw new Error(errorMsg);
                  }
                } catch (error: any) {
                  console.error('[SendSEKA] Error:', error);
                  alert('❌ Transfer failed:\n\n' + (error.message || error));
                } finally {
                  setSending(false);
                }
              }}
              disabled={sending || !sendTo || !sendAmount}
              className="w-full"
            >
              {sending ? 'Sending...' : 'Send SEKA'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* System Stats */}
      <Card>
        <CardHeader>
          <CardTitle>System Stats</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Auto-Mint Status:</span>
            <Badge variant="default" className="bg-green-500">Active</Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Check Interval:</span>
            <span className="font-medium">30 seconds</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Log Rotation:</span>
            <span className="font-medium">30 seconds</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Burst Protection:</span>
            <span className="font-medium">Disabled</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
