import pytest
from agent.main import ip_hash, EWMA, WindowStats, parse_mqtt


def test_ip_hash():
    result = ip_hash("192.168.1.1", "test-salt")
    assert result.startswith("iphash:")
    assert len(result) == 19


def test_ewma_initialization():
    ewma = EWMA(alpha=0.2)
    assert ewma.mu is None
    assert ewma.var == 1e-6


def test_ewma_update():
    ewma = EWMA(alpha=0.2)
    ewma.update(10.0)
    assert ewma.mu == 10.0
    ewma.update(20.0)
    assert ewma.mu > 10.0


def test_window_stats():
    ws = WindowStats()
    ws.add(100.0, False)
    ws.add(200.0, True)
    p95, err_rate, z_lat, z_err = ws.snapshot()
    assert ws.calls == 2
    assert ws.errs == 1
    assert err_rate == 0.5


def test_parse_mqtt():
    host, port, tls = parse_mqtt("mqtt://localhost:1883")
    assert host == "localhost"
    assert port == 1883
    assert tls is False
    
    host, port, tls = parse_mqtt("mqtts://broker:8883")
    assert host == "broker"
    assert port == 8883
    assert tls is True
