import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Coins, Clock, ExternalLink, Hash, Eye } from 'lucide-react';
import { nftAPI, type NFTMapping } from '../services/api';

export function NFTsPanel() {
  const [nfts, setNfts] = useState<NFTMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadNFTs();
    const interval = setInterval(loadNFTs, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const loadNFTs = async () => {
    try {
      const allNFTs = await nftAPI.getMappings();
      setTotal(allNFTs.length);
      // Get last 100 NFTs
      const latest = allNFTs
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, 100);
      setNfts(latest);
    } catch (error) {
      console.error('Failed to load NFTs:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Network NFTs</h3>
          <p className="text-sm text-muted-foreground">
            Showing {nfts.length} of {total} total minted NFTs
          </p>
        </div>
        <Badge variant="outline" className="text-lg px-4 py-2">
          <Coins className="h-4 w-4 mr-2" />
          {total} Total
        </Badge>
      </div>

      {nfts.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No NFTs minted yet
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {nfts.map((nft, idx) => (
            <Card key={idx}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-base">{nft.filename}</CardTitle>
                    <CardDescription className="flex items-center gap-2">
                      <Clock className="h-3 w-3" />
                      {new Date(nft.timestamp * 1000).toLocaleString()}
                    </CardDescription>
                  </div>
                  <Badge variant="default">
                    <Coins className="h-3 w-3 mr-1" />
                    Minted
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground mb-1">Hash</p>
                    <div className="flex items-center gap-2 font-mono text-xs bg-muted p-2 rounded">
                      <Hash className="h-3 w-3" />
                      {nft.hash.substring(0, 32)}...
                    </div>
                  </div>
                  <div>
                    <p className="text-muted-foreground mb-1">Transaction</p>
                    <div className="flex items-center gap-2 font-mono text-xs bg-muted p-2 rounded">
                      <ExternalLink className="h-3 w-3" />
                      {nft.nft_tx.substring(0, 32)}...
                    </div>
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground text-sm mb-1">Log URL</p>
                  <a 
                    href={nft.log_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline flex items-center gap-1"
                  >
                    {nft.log_url}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={async () => {
                    try {
                      // Extract log ID from URL
                      const logId = nft.log_url.split('/').pop();
                      const response = await fetch(`/api/view_log/${logId}`);
                      const data = await response.json();
                      alert(JSON.stringify(data, null, 2));
                    } catch (error) {
                      alert('Failed to load NFT data: ' + error);
                    }
                  }}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View NFT Data
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
