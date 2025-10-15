from typing import Dict, List


class AttackClassifier:
    """Classify attack types from log patterns"""
    
    ATTACK_TYPES = {
        'ddos': 'Distributed Denial of Service',
        'resource_exhaustion': 'Resource Exhaustion Attack',
        'scanning': 'Port/Service Scanning',
        'credential_stuffing': 'Credential Stuffing',
        'rate_abuse': 'Rate Limit Abuse',
        'unknown': 'Unknown Attack Pattern'
    }
    
    SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical']
    
    @staticmethod
    def classify(log_data: dict) -> dict:
        """
        Classify attack type from log data
        
        Returns:
        {
            'type': str,
            'severity': str,
            'confidence': float,
            'recommended_action': str,
            'indicators': list
        }
        """
        metrics = log_data.get('metrics', {})
        z_scores = log_data.get('z', {})
        method = log_data.get('method', '')
        
        requests = metrics.get('calls', 0)
        err_rate = metrics.get('err_rate', 0.0)
        p95 = metrics.get('p95', 0.0)
        z_lat = z_scores.get('lat', 0.0)
        z_err = z_scores.get('err', 0.0)
        
        indicators = []
        
        # DDoS: High volume, relatively normal error rate
        if requests > 1000 and err_rate < 0.15:
            indicators.append(f'High volume: {requests} requests')
            indicators.append(f'Low error rate: {err_rate:.2%}')
            return {
                'type': 'ddos',
                'severity': 'critical' if requests > 5000 else 'high',
                'confidence': 0.9,
                'recommended_action': 'block_ips_immediately',
                'indicators': indicators
            }
        
        # Resource Exhaustion: Heavy methods with high latency
        heavy_methods = ['getProgramAccounts', 'getLogs', 'getSignaturesForAddress']
        if method in heavy_methods and (z_lat > 4.0 or p95 > 500):
            indicators.append(f'Heavy method: {method}')
            indicators.append(f'High latency: p95={p95:.0f}ms, z={z_lat:.1f}')
            return {
                'type': 'resource_exhaustion',
                'severity': 'high',
                'confidence': 0.85,
                'recommended_action': 'rate_limit_heavy_methods',
                'indicators': indicators
            }
        
        # Scanning/Fuzzing: Very high error rate
        if err_rate > 0.3:
            indicators.append(f'High error rate: {err_rate:.2%}')
            indicators.append(f'Error z-score: {z_err:.1f}')
            return {
                'type': 'scanning',
                'severity': 'medium' if err_rate < 0.5 else 'high',
                'confidence': 0.8,
                'recommended_action': 'block_ips_temporary',
                'indicators': indicators
            }
        
        # Credential Stuffing: Auth failures
        if 'auth' in method.lower() and err_rate > 0.5:
            indicators.append(f'Auth method: {method}')
            indicators.append(f'High failure rate: {err_rate:.2%}')
            return {
                'type': 'credential_stuffing',
                'severity': 'high',
                'confidence': 0.75,
                'recommended_action': 'block_ips_and_alert',
                'indicators': indicators
            }
        
        # Rate Abuse: Moderate volume with some errors
        if requests > 500 and 0.05 < err_rate < 0.3:
            indicators.append(f'Moderate volume: {requests} requests')
            indicators.append(f'Moderate errors: {err_rate:.2%}')
            return {
                'type': 'rate_abuse',
                'severity': 'medium',
                'confidence': 0.7,
                'recommended_action': 'rate_limit',
                'indicators': indicators
            }
        
        # Unknown pattern
        indicators.append(f'Requests: {requests}')
        indicators.append(f'Error rate: {err_rate:.2%}')
        indicators.append(f'P95 latency: {p95:.0f}ms')
        return {
            'type': 'unknown',
            'severity': 'low',
            'confidence': 0.5,
            'recommended_action': 'monitor',
            'indicators': indicators
        }
    
    @staticmethod
    def get_severity_score(severity: str) -> int:
        """Convert severity to numeric score"""
        scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        return scores.get(severity, 0)
    
    @staticmethod
    def should_auto_block(classification: dict, min_confidence: float = 0.7) -> bool:
        """Determine if attack should trigger automatic blocking"""
        if classification['confidence'] < min_confidence:
            return False
        
        severity = classification['severity']
        if severity in ['high', 'critical']:
            return True
        
        return False
    
    @staticmethod
    def format_report(classification: dict) -> str:
        """Format classification as human-readable report"""
        lines = [
            f"Attack Type: {classification['type'].upper()}",
            f"Severity: {classification['severity'].upper()}",
            f"Confidence: {classification['confidence']:.0%}",
            f"Recommended Action: {classification['recommended_action']}",
            "",
            "Indicators:"
        ]
        
        for indicator in classification['indicators']:
            lines.append(f"  - {indicator}")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test cases
    test_cases = [
        {
            'name': 'DDoS Attack',
            'data': {
                'metrics': {'calls': 5000, 'err_rate': 0.05, 'p95': 150},
                'z': {'lat': 2.0, 'err': 1.5},
                'method': 'getBalance'
            }
        },
        {
            'name': 'Resource Exhaustion',
            'data': {
                'metrics': {'calls': 200, 'err_rate': 0.1, 'p95': 600},
                'z': {'lat': 8.0, 'err': 2.0},
                'method': 'getProgramAccounts'
            }
        },
        {
            'name': 'Scanning',
            'data': {
                'metrics': {'calls': 300, 'err_rate': 0.6, 'p95': 100},
                'z': {'lat': 1.0, 'err': 5.0},
                'method': 'getBlock'
            }
        }
    ]
    
    classifier = AttackClassifier()
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print('='*60)
        
        classification = classifier.classify(test['data'])
        print(classifier.format_report(classification))
        print(f"\nAuto-block: {classifier.should_auto_block(classification)}")
