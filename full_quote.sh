#!/bin/bash
# Full end-to-end quote pipeline:
#   1. Generate PDF (generate_quote.sh)
#   2. Post to Discord (handled by generate_quote.sh)
#   3. Create Gmail draft in southern.barn.services@gmail.com with the PDF attached
#
# All the same args as generate_quote.sh. Adds:
#   --no-email   skip the email draft step
#   --first-name "First"   overrides the first name used in "Hi X,"
#
# Examples:
#   ./full_quote.sh --name "Nathan Bloom" --email "Nrb.nrb@icloud.com" \
#      --city "Lake Butler" --state "FL" --num "SBB-Q-004" \
#      --kit-desc "40x60x12 Pole Barn Kit — Complete Materials Package" \
#      --subtotal 14000
#
#   ./full_quote.sh --name "Art Johnson" --email "slingshot1943@yahoo.com" \
#      --city "Live Oak" --state "FL" --num "SBB-Q-011" \
#      --kit-desc "40x60x12 Pole Barn Kit — Complete Materials Package" \
#      --subtotal 14500 --travel-price 500

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="C:/Users/joshu/OneDrive/Pictures/Screenshots 1/Southern Barn Services"

# Parse out the args we need for the email step; pass everything else through to generate_quote.sh
NAME=""
EMAIL=""
CITY=""
STATE=""
NUM=""
KIT_DESC=""
KIT_PRICE=""
SUBTOTAL=""
TRAVEL_PRICE=""
LABOR_PRICE=""
OUTPUT=""
FIRST_NAME=""
NO_EMAIL=""
PASSTHRU=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --email) EMAIL="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --city) CITY="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --state) STATE="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --num) NUM="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --kit-desc) KIT_DESC="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --kit-price) KIT_PRICE="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --subtotal) SUBTOTAL="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --travel-price) TRAVEL_PRICE="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --labor-price) LABOR_PRICE="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --output) OUTPUT="$2"; PASSTHRU+=("$1" "$2"); shift 2;;
    --first-name) FIRST_NAME="$2"; shift 2;;
    --no-email) NO_EMAIL="1"; shift;;
    *) PASSTHRU+=("$1"); shift;;
  esac
done

# Default PDF output path matches generate_quote.sh's default
if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$OUTPUT_DIR/INVOICE $NAME.pdf"
fi

# --- Step 1 & 2: Generate PDF and post to Discord ---
"$SCRIPT_DIR/generate_quote.sh" "${PASSTHRU[@]}"

# --- Step 3: Create Gmail draft ---
if [[ -n "$NO_EMAIL" ]]; then
  echo "Skipping email draft step (--no-email)."
  exit 0
fi

if [[ -z "$EMAIL" ]]; then
  echo "No customer email provided; skipping email draft step."
  exit 0
fi

# Default first name: first token of full name
if [[ -z "$FIRST_NAME" ]]; then
  FIRST_NAME=$(echo "$NAME" | awk '{print $1}')
fi

# Decide document type from invoice number
DOC_TYPE="INVOICE"
if [[ "$NUM" =~ [Qq] ]]; then DOC_TYPE="QUOTE"; fi

# Compute totals using the same math as the Discord summary
export SB_KIT_PRICE="${KIT_PRICE:-0}"
export SB_LABOR_PRICE="${LABOR_PRICE:-5487.50}"
export SB_TRAVEL_PRICE="${TRAVEL_PRICE:-350}"
export SB_SUBTOTAL_ARG="${SUBTOTAL:-0}"

read_totals=$(python -c "
import os
sub_arg = float(os.environ['SB_SUBTOTAL_ARG'])
kit = float(os.environ['SB_KIT_PRICE'])
labor = float(os.environ['SB_LABOR_PRICE'])
travel = float(os.environ['SB_TRAVEL_PRICE'])
# If --subtotal was used, the script back-calculates kit/labor. For the email
# we just use the canonical total = subtotal + travel (plus tax-on-deposit math).
if sub_arg > 0:
    pre_travel = sub_arg
else:
    pre_travel = kit + labor
full_subtotal = pre_travel + travel
deposit = full_subtotal * 0.5
tax = deposit * 0.07
total_now = deposit + tax
print(f'{full_subtotal:.2f}|{deposit:.2f}|{tax:.2f}|{total_now:.2f}')
")
IFS='|' read -r FULL_SUBTOTAL DEPOSIT TAX TOTAL_NOW <<< "$read_totals"

# Location phrase for email body
LOCATION_LINE=""
if [[ -n "$CITY" && -n "$STATE" ]]; then
  LOCATION_LINE=" with delivery and installation to $CITY, $STATE"
elif [[ -n "$CITY" ]]; then
  LOCATION_LINE=" with delivery and installation to $CITY"
fi

SUBJECT="Your Pole Barn $([ "$DOC_TYPE" = "QUOTE" ] && echo Quote || echo Invoice) — $KIT_DESC | Southern Barn Builders LLC"

# Trim KIT_DESC for subject (just take the dimensions if it's long)
SHORT_KIT=$(echo "$KIT_DESC" | grep -oE '[0-9]+x[0-9]+(x[0-9]+)?' | head -1)
if [[ -n "$SHORT_KIT" ]]; then
  SUBJECT="Your Pole Barn $([ "$DOC_TYPE" = "QUOTE" ] && echo Quote || echo Invoice) — ${SHORT_KIT} | Southern Barn Builders LLC"
fi

BODY="Hi $FIRST_NAME,

Good talking with you. Attached is your $([ "$DOC_TYPE" = "QUOTE" ] && echo quote || echo invoice) for the $KIT_DESC$LOCATION_LINE.

Quick summary:
  Subtotal: \$$FULL_SUBTOTAL
  50% Deposit Due Now (incl. 7% sales tax): \$$TOTAL_NOW

The kit includes 6x6 or 8x8 marine-grade treated posts (thru-bolted trusses), 2x6 purlins, 29-gauge metal roofing and siding (upgradeable to 26-gauge), and 2\" angle iron steel trusses rated for 150 mph winds. All materials, materials tax, delivery, and installation are included. Concrete is not included unless otherwise noted.

The 50% deposit secures your project slot and gets us moving on material procurement and scheduling. Balance is due at completion. We accept check, cash, Zelle, or bank transfer.

Take a look at the attached $([ "$DOC_TYPE" = "QUOTE" ] && echo quote || echo invoice) and let me know if you have any questions or want to move forward.

Thanks $FIRST_NAME — looking forward to building for you.

Carson
Southern Barn Builders LLC
(352) 646-9090
southern.barn.services@gmail.com"

echo ""
echo "Creating Gmail draft..."
"$SCRIPT_DIR/send_email.sh" \
  --to "$EMAIL" \
  --subject "$SUBJECT" \
  --body "$BODY" \
  --attachment "$OUTPUT"
