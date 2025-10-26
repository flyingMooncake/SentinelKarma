#!/bin/bash
# Test script to generate burst traffic for auto-mint testing

echo "🔥 Overburst Test Script"
echo "========================"
echo ""

# Create test logs directory
LOGS_DIR="./data/malicious_logs"
mkdir -p "$LOGS_DIR"

echo "[INFO] Creating test log files in $LOGS_DIR"
echo ""

# Function to create a test log file
create_test_log() {
    local timestamp=$1
    local filename="${LOGS_DIR}/${timestamp}_26_01_25_12_30_00.log"
    
    cat > "$filename" << EOF
{
  "v": 1,
  "sid": 0,
  "t": ${timestamp},
  "cnt": 5,
  "cap": 10,
  "region": "test",
  "asn": "AS12345",
  "requests": 1000,
  "unique_iphash": 5,
  "avg_err_rate": 0.15,
  "top_attackers": [
    {"iphash": "abc123def456", "requests": 500, "err_rate": 0.2},
    {"iphash": "789ghi012jkl", "requests": 300, "err_rate": 0.15},
    {"iphash": "mno345pqr678", "requests": 200, "err_rate": 0.1}
  ]
}
EOF
    
    echo "  ✓ Created: $(basename $filename)"
}

# Test 1: Normal operation (3 files, spaced out)
echo "Test 1: Normal Operation (3 files)"
echo "-----------------------------------"
for i in {1..3}; do
    timestamp=$((1700000000 + i))
    create_test_log $timestamp
    sleep 1
done
echo ""

# Wait a bit
echo "[WAIT] Waiting 5 seconds before burst test..."
sleep 5
echo ""

# Test 2: Burst (6 files rapidly)
echo "Test 2: Burst Test (6 files in <1 second)"
echo "------------------------------------------"
echo "This should trigger burst protection!"
echo ""

for i in {10..15}; do
    timestamp=$((1700000000 + i))
    create_test_log $timestamp
done

echo ""
echo "✅ Test files created!"
echo ""
echo "📊 Summary:"
echo "  - Normal: 3 files (spaced 1s apart)"
echo "  - Burst: 6 files (all at once)"
echo "  - Total: 9 test files"
echo ""
echo "🚀 Now run the auto-mint monitor:"
echo "   python3 scripts/auto_mint_complete.py"
echo ""
echo "Expected behavior:"
echo "  1. Process first 3 files normally"
echo "  2. Start processing burst files"
echo "  3. After 5 files in 5s → BURST DETECTED"
echo "  4. Enter 10s cooldown"
echo "  5. Resume after cooldown"
