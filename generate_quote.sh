#!/bin/bash
# Autonomous quote-PDF generator.
# Uses Chrome headless + the existing invoice-generator.html template.
# Usage example:
#   ./generate_quote.sh \
#     --name "Nathan Bloom" \
#     --email "Nrb.nrb@icloud.com" \
#     --city "Lake Butler" --state "FL" \
#     --num "SBB-Q-004" \
#     --kit-desc "40x60x12 Pole Barn Kit (8x8 Posts) — Complete Materials Package" \
#     --kit-price 8500

set -e

CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe"
BASE_URL="http://localhost:8080/invoice-generator.html"
OUTPUT_DIR="C:/Users/joshu/OneDrive/Pictures/Screenshots 1/Southern Barn Services"

# Defaults
LABOR_PRICE="5487.50"
TRAVEL_PRICE="350"
NUM="SBB-Q-NEW"
NAME=""
EMAIL=""
CITY=""
STATE=""
KIT_DESC=""
KIT_PRICE=""
OUTPUT=""
NO_POST=""
NOTES=""
EXTRA_ITEMS=()
SUBTOTAL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2;;
    --email) EMAIL="$2"; shift 2;;
    --city) CITY="$2"; shift 2;;
    --state) STATE="$2"; shift 2;;
    --num) NUM="$2"; shift 2;;
    --kit-desc) KIT_DESC="$2"; shift 2;;
    --kit-price) KIT_PRICE="$2"; shift 2;;
    --subtotal) SUBTOTAL="$2"; shift 2;;
    --extra-item) EXTRA_ITEMS+=("$2"); shift 2;;
    --labor-price) LABOR_PRICE="$2"; shift 2;;
    --travel-price) TRAVEL_PRICE="$2"; shift 2;;
    --output) OUTPUT="$2"; shift 2;;
    --notes) NOTES="$2"; shift 2;;
    --no-post) NO_POST="1"; shift;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

# If --subtotal is given, randomly split kit + labor so both look calculated
# and unique per quote. labor picks a random value in a small window;
# kit = subtotal - labor - (extras).
if [[ -n "$SUBTOTAL" ]]; then
  EXTRAS_PIPE_SUM=$(IFS=$'\x1f'; echo "${EXTRA_ITEMS[*]}")
  export SB_EXTRAS_SUM_IN="$EXTRAS_PIPE_SUM"
  export SB_SUBTOTAL="$SUBTOTAL"
  read_out=$(python -c "
import os, random
subtotal = float(os.environ['SB_SUBTOTAL'])
raw = os.environ.get('SB_EXTRAS_SUM_IN','')
extras_sum = 0.0
if raw:
    for entry in raw.split('\x1f'):
        if '|' in entry:
            _, price = entry.rsplit('|', 1)
            try: extras_sum += float(price)
            except: pass
# Labor range $5,430.00 - $5,549.99 with cents → always looks calculated & unique
labor = round(random.uniform(5430, 5549.99), 2)
kit = round(subtotal - labor - extras_sum, 2)
print(f'{kit:.2f} {labor:.2f}')
")
  KIT_PRICE=$(echo "$read_out" | awk '{print $1}')
  LABOR_PRICE=$(echo "$read_out" | awk '{print $2}')
fi

if [[ -z "$NAME" || -z "$KIT_DESC" || -z "$KIT_PRICE" ]]; then
  echo "ERROR: --name, --kit-desc, and --kit-price are required"
  exit 1
fi

# Default output filename: "INVOICE {name}.pdf" in the project folder
if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$OUTPUT_DIR/INVOICE $NAME.pdf"
fi

# URL-encode with Python
urlenc() {
  python -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"
}

# Build items JSON via Python so special chars in descs are escaped safely
export SB_KIT_DESC="$KIT_DESC"
export SB_KIT_PRICE="$KIT_PRICE"
export SB_LABOR_PRICE="$LABOR_PRICE"
export SB_TRAVEL_PRICE="$TRAVEL_PRICE"
EXTRAS_PIPE=$(IFS=$'\x1f'; echo "${EXTRA_ITEMS[*]}")
export SB_EXTRAS="$EXTRAS_PIPE"

ITEMS_JSON=$(python -c "
import json, os
items = [{'desc': os.environ['SB_KIT_DESC'], 'qty': 1, 'price': float(os.environ['SB_KIT_PRICE'])}]
raw = os.environ.get('SB_EXTRAS','')
if raw:
    for entry in raw.split('\x1f'):
        if '|' in entry:
            desc, price = entry.rsplit('|', 1)
            items.append({'desc': desc, 'qty': 1, 'price': float(price)})
items.append({'desc': 'Professional Installation & Labor', 'qty': 1, 'price': float(os.environ['SB_LABOR_PRICE'])})
items.append({'desc': 'Travel & Site Mobilization', 'qty': 1, 'price': float(os.environ['SB_TRAVEL_PRICE'])})
print(json.dumps(items))
")

URL="$BASE_URL"
URL+="?num=$(urlenc "$NUM")"
URL+="&name=$(urlenc "$NAME")"
URL+="&email=$(urlenc "$EMAIL")"
URL+="&city=$(urlenc "$CITY")"
URL+="&state=$(urlenc "$STATE")"
URL+="&items=$(urlenc "$ITEMS_JSON")"
if [[ -n "$NOTES" ]]; then
  URL+="&notes=$(urlenc "$NOTES")"
fi

echo "Generating PDF..."
echo "  Customer: $NAME"
echo "  Output:   $OUTPUT"

"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --virtual-time-budget=5000 \
  --print-to-pdf="$OUTPUT" \
  "$URL" 2>/dev/null

if [[ -f "$OUTPUT" ]]; then
  echo "Done. PDF saved to: $OUTPUT"
else
  echo "ERROR: PDF was not created."
  exit 1
fi

# ---------- Discord webhook post ----------
WEBHOOK_FILE="$OUTPUT_DIR/.discord_webhook"
if [[ -z "$NO_POST" && -f "$WEBHOOK_FILE" ]]; then
  WEBHOOK_URL=$(head -n 1 "$WEBHOOK_FILE" | tr -d '\r\n')
  if [[ -n "$WEBHOOK_URL" ]]; then
    export SB_NAME="$NAME"
    export SB_NUM="$NUM"
    export SB_KIT_DESC="$KIT_DESC"
    export SB_ITEMS_JSON="$ITEMS_JSON"

    PAYLOAD_JSON=$(python -c "
import json, os
name = os.environ['SB_NAME']
num = os.environ['SB_NUM']
kit = os.environ['SB_KIT_DESC']
items = json.loads(os.environ['SB_ITEMS_JSON'])
subtotal = sum(i['qty'] * i['price'] for i in items)
deposit = subtotal * 0.5
tax = deposit * 0.07
total_now = deposit + tax
doc_type = 'QUOTE' if 'Q' in num.upper().split('-') else 'INVOICE'
content = (
    f'**New {doc_type} — {name}** ({num})\n'
    f'{kit}\n'
    f'Subtotal: \${subtotal:,.2f} · Deposit (50%): \${deposit:,.2f} · Tax (7%): \${tax:,.2f}\n'
    f'**Total Due Now: \${total_now:,.2f}**'
)
print(json.dumps({'content': content}))
")

    echo "Posting to Discord..."
    HTTP_CODE=$(curl -s -o /tmp/discord_resp.txt -w "%{http_code}" \
      -F "payload_json=$PAYLOAD_JSON" \
      -F "file1=@$OUTPUT" \
      "$WEBHOOK_URL")
    if [[ "$HTTP_CODE" =~ ^2 ]]; then
      echo "Posted to Discord (HTTP $HTTP_CODE)."
    else
      echo "Discord post failed (HTTP $HTTP_CODE):"
      cat /tmp/discord_resp.txt
      echo ""
    fi
  fi
fi
