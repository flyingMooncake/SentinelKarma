#!/bin/bash
# Transfer SEKA tokens
# Usage: ./transfer_seka.sh <recipient> <amount>

RECIPIENT=$1
AMOUNT=$2
SEKA_MINT="82UjXqRTyzNxkchsrwNmA7KgWgPFQ1QDDpUVo37ar6qE"

if [ -z "$RECIPIENT" ] || [ -z "$AMOUNT" ]; then
    echo '{"success":false,"error":"Missing recipient or amount"}'
    exit 1
fi

# Execute transfer
OUTPUT=$(spl-token transfer "$SEKA_MINT" "$AMOUNT" "$RECIPIENT" --fund-recipient --allow-unfunded-recipient 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    # Extract signature
    SIGNATURE=$(echo "$OUTPUT" | grep "Signature:" | awk '{print $2}')
    echo "{\"success\":true,\"signature\":\"$SIGNATURE\",\"amount\":$AMOUNT,\"recipient\":\"$RECIPIENT\"}"
else
    ERROR=$(echo "$OUTPUT" | tr '\n' ' ' | sed 's/"/\\"/g')
    echo "{\"success\":false,\"error\":\"$ERROR\"}"
    exit 1
fi
