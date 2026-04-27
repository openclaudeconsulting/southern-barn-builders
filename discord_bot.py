#!/usr/bin/env python3
"""
Southern Barn Quote Bot.

Listens to the #to-do Discord channel. On each new message:
  1. Reacts with 👀 to show processing
  2. Calls Claude API to parse the customer info into structured JSON
  3. Runs full_quote.sh for each quote (supports multi-variant inquiries like Dan's 29ga/26ga)
  4. Reacts with ✅ on success, ❌ on failure, ❓ if the message doesn't look like a quote request

Credentials:
  <project_root>/.discord_bot.env      — DISCORD_BOT_TOKEN + DISCORD_TODO_CHANNEL_ID
  <project_root>/.anthropic_api_key    — Claude API key (single line)
  <project_root>/.invoice_counter      — Tracks next invoice number (auto-created)
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------- Bash discovery ----------
# When the bot runs under a Windows scheduled task, the PATH it inherits picks
# up C:\Windows\System32\bash.exe (WSL launcher) before Git Bash, and WSL's
# /bin/bash exec fails (no distro). Resolve Git Bash explicitly so we always
# invoke the same shell Carson uses interactively, regardless of how the bot
# was started.
GIT_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
)


def resolve_bash() -> str:
    """Return an absolute path to a usable bash.exe (Git Bash preferred)."""
    for candidate in GIT_BASH_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    # Last resort: whatever 'bash' resolves to on PATH. Skip the WSL launcher
    # in System32 which crashes when invoked without a distro.
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        return found
    raise FileNotFoundError(
        "Could not locate a usable bash.exe. Install Git for Windows "
        "(which provides C:\\Program Files\\Git\\bin\\bash.exe) and rerun."
    )


BASH_EXE = resolve_bash()

# Force UTF-8 stdout/stderr so emoji characters in Discord messages don't
# crash the Windows cp1252 console when printed.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import discord
from anthropic import Anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".discord_bot.env"
API_KEY_FILE = PROJECT_ROOT / ".anthropic_api_key"
INVOICE_COUNTER_FILE = PROJECT_ROOT / ".invoice_counter"
INVOICE_LOG_FILE = PROJECT_ROOT / ".invoice_log.jsonl"
SCRIPT_DIR = Path(__file__).resolve().parent
FULL_QUOTE_SCRIPT = SCRIPT_DIR / "full_quote.sh"


def append_invoice_log(record: dict) -> None:
    """Append one JSON record per successful quote. Consumed by barn-accounting bot."""
    try:
        with INVOICE_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"WARN: could not append to {INVOICE_LOG_FILE}: {e}", flush=True)


def invoice_num_from_args(args: list[str]) -> str:
    try:
        i = args.index("--num")
        return args[i + 1]
    except (ValueError, IndexError):
        return ""

# ---------- Load config ----------
def load_env():
    if not ENV_FILE.exists():
        sys.exit(f"ERROR: {ENV_FILE} not found. Create it with DISCORD_BOT_TOKEN and DISCORD_TODO_CHANNEL_ID.")
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    for required in ("DISCORD_BOT_TOKEN", "DISCORD_TODO_CHANNEL_ID"):
        if required not in env:
            sys.exit(f"ERROR: {required} missing from {ENV_FILE}")
    return env


def load_api_key():
    if not API_KEY_FILE.exists():
        sys.exit(f"ERROR: {API_KEY_FILE} not found. Paste your Anthropic API key into that file (single line).")
    key = API_KEY_FILE.read_text(encoding="utf-8").strip()
    if not key.startswith("sk-ant-"):
        sys.exit(f"ERROR: {API_KEY_FILE} doesn't look like a valid Anthropic API key (should start with 'sk-ant-').")
    return key


# ---------- Invoice numbering ----------
STARTING_INVOICE = 11  # Last manually-assigned was SBB-Q-011 (Art Johnson)
INVOICE_PREFIX = "GP-Q"  # Brand-matched prefix (was SBB-Q under prior brand)

def next_invoice_num():
    if INVOICE_COUNTER_FILE.exists():
        try:
            n = int(INVOICE_COUNTER_FILE.read_text().strip())
        except ValueError:
            n = STARTING_INVOICE
    else:
        n = STARTING_INVOICE
    n += 1
    INVOICE_COUNTER_FILE.write_text(str(n))
    return f"{INVOICE_PREFIX}-{n:03d}"


# ---------- Claude parser ----------
PARSE_SYSTEM_PROMPT = """You are a parser for G&P Steel Trusses customer quote requests posted in a Discord channel by Carson (the sales rep).

Your job: read Carson's free-form message and return STRICT JSON describing one or more quotes to generate.

### Business pricing rules (baked into the pipeline — reference only, don't re-encode prices):
- Labor defaults to ~$5,500 (randomized with cents by the script; never hardcode labor in kit price).
- Travel defaults to $350. Only override if Carson explicitly says "delivery 500" or similar.
- Standard 40x60 base kit = $8,500. Upgrades get folded into the kit price numerically; you do NOT break them out as separate line items.
- Always include the travel fee.

### Output schema (strict JSON only, no prose, no markdown fences):
{
  "confidence": "high" | "low",
  "skip": boolean,
  "explanation": "one-sentence note about what you inferred (for logs)",
  "quotes": [
    {
      "name": "Full Name",
      "first_name": "First",
      "email": "a@b.com",
      "city": "City name or empty string",
      "state": "FL or GA etc, or empty string",
      "kit_desc": "e.g. '40x60x12 Pole Barn Kit — Complete Materials Package' — fold upgrades like (26ga Metal Upgrade) or (14' Bays) in parentheses into this description; do NOT mention 8x8 posts (not significant) or 29ga (standard)",
      "subtotal": 14000,
      "kit_price": null,
      "labor_price": null,
      "quantity": 1,
      "travel_price_override": null,
      "tax_rate": null,
      "deposit_pct": null,
      "variant_label": null,
      "needs_26ga_disclaimer": false,
      "needs_20ft_disclaimer": false
    }
  ]
}

### Rules:
- **Price capture** — TWO modes, pick one per quote:
  - **Explicit split**: If Carson lists a kit price AND a separate install/labor price (e.g. "Kit $4,850 / Install $3,000" or "9000$ kit / 5500$ install"), set `kit_price` and `labor_price` to those exact numbers and set `subtotal` to null. The script will honor them verbatim — no randomization. Use this any time the post shows both numbers separately.
  - **Combined total**: If Carson gives a single lump total (e.g. "40x60x12 : 14,500") without splitting kit vs install, set `subtotal` to that number and leave `kit_price` and `labor_price` null. The script randomizes labor in the ~$5,500 range and back-fills kit. **Only safe for standard 40x60-class kits where ~$5,500 labor is reasonable.** Smaller kits like 30x36 need the explicit split mode.
  - All prices are **per-unit**. If quantity > 1, the template multiplies the kit line automatically — do NOT pre-multiply and hand Claude a grand total.
- `quantity` = number of IDENTICAL barns being quoted on the SAME quote. Default 1. Set >1 ONLY when Carson explicitly says things like "5 of these", "x5", "quantity 5", "five barns". Never block a quote for missing quantity — if it's not mentioned, quantity is 1. If Carson wants DIFFERENT-sized barns for the same customer, those are separate `quotes` entries, not quantity.
- `travel_price_override` = only a number if Carson explicitly stated a delivery/travel fee (like "Delivery 500$"). Otherwise null.
- `tax_rate` = Default is 0 (no sales tax, line hidden). ONLY set a number if Carson EXPLICITLY asks for tax — e.g. "7% tax", "add sales tax", "tax this one at 6%". A generic phrase like "Florida project" is NOT a reason to add tax. Leave null unless the to-do post literally mentions adding/including tax with a percentage. Never guess.
- `deposit_pct` = ONLY set if Carson explicitly overrides the default 50% deposit. Otherwise null.
- `needs_26ga_disclaimer` = true if the quote uses 26ga metal (the quote template will include the manufacturer-inquiry disclaimer text).
- `needs_20ft_disclaimer` = true if height is 20' or taller.
- If the inquiry has multiple variants (e.g. "Wants price on 29ga & 26ga"), output multiple entries in `quotes`, one per variant. Set `variant_label` to "29ga", "26ga", etc.
- If the message doesn't look like a quote request at all (e.g. just chatter, a question, a status update), set `skip: true` and `quotes: []`.
- **Only a first name and a price are required.** Email, last name, city, and state are ALL optional. If a first name (or any name) and a price are present, treat the quote as high confidence — never set `confidence: "low"` just because email or last name is missing. Use empty string `""` for any missing string field. Email missing is fine — the pipeline will skip the Gmail draft step and still produce the PDF + Discord post. Only set `confidence: "low"` when something truly blocking is missing (no price at all, no dimensions, or the message is ambiguous about what's being quoted).
- NEVER include permitting, rebar, or concrete language in the kit_desc even if the customer mentions them — Carson has to explicitly approve those inclusions separately.

Return ONLY the JSON object. No explanations before or after."""


def parse_with_claude(claude_client: Anthropic, text: str) -> dict:
    resp = claude_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=PARSE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = resp.content[0].text.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON: {raw[:300]}") from e


# ---------- Dispatcher ----------
TWENTY_SIX_GA_NOTES = (
    "50% deposit is due upon receipt. The deposit secures your project slot and material procurement. "
    "Concrete and rebar are not included unless listed as a line item. Balance due at project completion. We accept check, cash, Zelle, or bank transfer.\n\n"
    "26ga pricing reflects current manufacturer inquiry rates and may adjust at order time. "
    "Ridge caps, eve drips, and eve trims are 26ga standard on every build (no upcharge). "
    "Thank you for choosing G&P Steel Trusses."
)

TWENTY_FT_NOTES = (
    "50% deposit is due upon receipt. The deposit secures your project slot and material procurement. "
    "Concrete and rebar are not included unless listed as a line item. Balance due at project completion. We accept check, cash, Zelle, or bank transfer.\n\n"
    "Pricing on structures 20' or taller is subject to manufacturer confirmation prior to order. "
    "Irregular sizes are affected by supply-chain and material-availability fluctuations; "
    "final price will be confirmed before the deposit is processed. "
    "Thank you for choosing G&P Steel Trusses."
)


def build_cmd_args(quote: dict) -> list[str]:
    """Build argv list for full_quote.sh from a parsed quote dict."""
    num = next_invoice_num()
    name = quote["name"]
    output_dir = PROJECT_ROOT
    variant = quote.get("variant_label")
    if variant:
        output_path = output_dir / f"INVOICE {name} {variant}.pdf"
    else:
        output_path = output_dir / f"INVOICE {name}.pdf"

    args = [
        "--name", name,
        "--email", quote.get("email", "") or "",
        "--city", quote.get("city", "") or "",
        "--state", quote.get("state", "") or "",
        "--num", num,
        "--kit-desc", quote["kit_desc"],
        "--output", str(output_path),
    ]
    # Pricing mode — pick the most explicit data Claude returned:
    #   1. Both kit + labor → pass both, no randomization.
    #   2. Kit only → pass --kit-price; the script uses its default labor
    #      (~$5,487.50). This handles "Kit 9000" posts where Carson didn't
    #      list a separate labor figure.
    #   3. Subtotal only → pass --subtotal; the script splits kit/labor.
    #   4. Nothing → raise (caller turns this into a ❌ reaction in Discord).
    kit_price = quote.get("kit_price")
    labor_price = quote.get("labor_price")
    subtotal = quote.get("subtotal")
    if kit_price is not None and labor_price is not None:
        args += ["--kit-price", str(kit_price), "--labor-price", str(labor_price)]
    elif kit_price is not None:
        args += ["--kit-price", str(kit_price)]
    elif subtotal is not None:
        args += ["--subtotal", str(subtotal)]
    else:
        raise ValueError("Quote is missing a price (need kit_price, labor_price, or subtotal)")
    if quote.get("first_name"):
        args += ["--first-name", quote["first_name"]]
    qty = quote.get("quantity")
    if qty is not None:
        try:
            qty_int = int(qty)
            if qty_int > 1:
                args += ["--qty", str(qty_int)]
        except (TypeError, ValueError):
            pass
    if quote.get("travel_price_override") is not None:
        args += ["--travel-price", str(quote["travel_price_override"])]
    if quote.get("tax_rate") is not None:
        args += ["--tax-rate", str(quote["tax_rate"])]
    if quote.get("deposit_pct") is not None:
        args += ["--deposit-pct", str(quote["deposit_pct"])]
    if quote.get("needs_26ga_disclaimer"):
        args += ["--notes", TWENTY_SIX_GA_NOTES]
    elif quote.get("needs_20ft_disclaimer"):
        args += ["--notes", TWENTY_FT_NOTES]
    return args


def run_full_quote(args: list[str], max_attempts: int = 2) -> tuple[bool, str]:
    """Run full_quote.sh with args. Retries once on failure with a 5s backoff
    so transient hiccups (HTTP server cold-start race, Chrome startup blip,
    momentary file lock) don't surface as ❌ to Carson. The same invoice number
    is reused across retries — a failed attempt doesn't post anything, so the
    retry just lands on Discord with the original number.

    Returns (success, combined_output).
    """
    last_output = ""
    for attempt in range(1, max_attempts + 1):
        try:
            result = subprocess.run(
                [BASH_EXE, str(FULL_QUOTE_SCRIPT), *args],
                capture_output=True,
                text=True,
                timeout=180,
            )
            last_output = result.stdout + ("\n" + result.stderr if result.stderr else "")
            if result.returncode == 0:
                if attempt > 1:
                    print(f"  -> succeeded on attempt {attempt}", flush=True)
                return True, last_output
            print(f"  -> attempt {attempt}/{max_attempts} failed (rc={result.returncode})", flush=True)
        except subprocess.TimeoutExpired:
            last_output = f"Timed out after 180 seconds (attempt {attempt})."
            print(f"  -> attempt {attempt}/{max_attempts} timed out", flush=True)
        except Exception as e:
            last_output = f"Unexpected error on attempt {attempt}: {type(e).__name__}: {e}"
            print(f"  -> attempt {attempt}/{max_attempts} crashed: {e}", flush=True)
        if attempt < max_attempts:
            time.sleep(5)
    return False, last_output


# ---------- Discord bot ----------
def build_bot(env: dict, claude_client: Anthropic) -> discord.Client:
    todo_channel_id = int(env["DISCORD_TODO_CHANNEL_ID"])
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Bot logged in as {client.user} (id {client.user.id})", flush=True)
        print(f"Listening to channel id {todo_channel_id}", flush=True)
        print(f"Bash binary       : {BASH_EXE}", flush=True)
        print(f"In {len(client.guilds)} guild(s):", flush=True)
        for g in client.guilds:
            print(f"  - {g.name} (id {g.id})", flush=True)
            for ch in g.text_channels:
                marker = " <-- TARGET" if ch.id == todo_channel_id else ""
                print(f"      #{ch.name} (id {ch.id}){marker}", flush=True)

    @client.event
    async def on_message(message: discord.Message):
        print(f"[msg] guild={message.guild.name if message.guild else 'DM'} #{message.channel.name if hasattr(message.channel,'name') else '?'} (id {message.channel.id}) author={message.author} text={message.content[:80]!r}", flush=True)
        # Ignore our own messages and non-target channels
        if message.author == client.user:
            return
        if message.channel.id != todo_channel_id:
            print(f"  -> ignored (wrong channel, want {todo_channel_id})", flush=True)
            return
        if not message.content.strip():
            return
        print(f"  -> processing with Claude...", flush=True)

        processing_reaction = "👀"
        try:
            await message.add_reaction(processing_reaction)
        except discord.HTTPException:
            pass

        try:
            parsed = await asyncio.to_thread(parse_with_claude, claude_client, message.content)
        except Exception as e:
            await message.add_reaction("❌")
            await message.reply(f"Parser error: `{type(e).__name__}: {e}`"[:1800])
            return

        if parsed.get("skip"):
            await message.add_reaction("🤷")
            await message.reply(f"Skipped (not a quote request): {parsed.get('explanation','')}"[:1800])
            try: await message.remove_reaction(processing_reaction, client.user)
            except: pass
            return

        if parsed.get("confidence") == "low":
            await message.add_reaction("❓")
            await message.reply(
                f"Low confidence parse — please handle manually via Claude Code.\n"
                f"Notes: {parsed.get('explanation','')}"[:1800]
            )
            try: await message.remove_reaction(processing_reaction, client.user)
            except: pass
            return

        quotes = parsed.get("quotes") or []
        if not quotes:
            await message.add_reaction("❓")
            await message.reply("Parser returned no quotes.")
            try: await message.remove_reaction(processing_reaction, client.user)
            except: pass
            return

        all_ok = True
        summary_lines = []
        for q in quotes:
            label = q.get("variant_label") or q.get("name", "quote")
            try:
                args = build_cmd_args(q)
            except Exception as e:
                all_ok = False
                summary_lines.append(f"❌ {label}: couldn't build quote — {type(e).__name__}: {e}")
                continue
            success, output = await asyncio.to_thread(run_full_quote, args)
            if success:
                append_invoice_log({
                    "invoice_num": invoice_num_from_args(args),
                    "name": q.get("name", ""),
                    "email": q.get("email", ""),
                    "city": q.get("city", ""),
                    "state": q.get("state", ""),
                    "kit_desc": q.get("kit_desc", ""),
                    "kit_price": q.get("kit_price"),
                    "labor_price": q.get("labor_price"),
                    "travel_price_override": q.get("travel_price_override"),
                    "subtotal": q.get("subtotal"),
                    "variant_label": q.get("variant_label"),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                summary_lines.append(f"✅ {label}: generated + posted + drafted")
            else:
                all_ok = False
                tail = output.strip().splitlines()[-5:]
                summary_lines.append(f"❌ {label}: failed\n```\n{chr(10).join(tail)}\n```")

        await message.add_reaction("✅" if all_ok else "❌")
        try: await message.remove_reaction(processing_reaction, client.user)
        except: pass

        reply = "\n".join(summary_lines)
        if parsed.get("explanation"):
            reply = f"_{parsed['explanation']}_\n{reply}"
        await message.reply(reply[:1950])

    return client


def main():
    env = load_env()
    api_key = load_api_key()
    claude_client = Anthropic(api_key=api_key)
    bot = build_bot(env, claude_client)
    bot.run(env["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    main()
