#!/usr/bin/env bash
# ============================================================
# OpenEnv Submission Validator
# Tests all 4 evaluation criteria — auto-starts server
# Usage: bash scripts/validate-submission.sh [port]
# ============================================================

PORT="${1:-7860}"
BASE="http://localhost:$PORT"
PASS=0
FAIL=0
SERVER_STARTED=false

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✅ PASS${NC} — $1"; ((PASS++)); }
fail() { echo -e "  ${RED}❌ FAIL${NC} — $1"; ((FAIL++)); }
info() { echo -e "  ${YELLOW}ℹ️  ${NC} $1"; }
hdr()  { echo -e "\n${BLUE}▶ $1${NC}"; }

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║    OpenEnv Customer Support — Submission Validator   ║"
echo "╚══════════════════════════════════════════════════════╝"

# ── Auto-start server if not running ─────────────────────────
echo ""
echo "Checking server at $BASE ..."
if ! curl -s --max-time 2 "$BASE/health" > /dev/null 2>&1; then
  echo -e "${YELLOW}⚡ Server not running — starting on port $PORT ...${NC}"

  # Find python/uvicorn
  if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
  elif command -v python3 &>/dev/null; then
    PYTHON="python3"
  else
    echo -e "${RED}❌ Python not found. Activate venv first.${NC}"
    exit 1
  fi

  $PYTHON -m uvicorn server.app:app --host 0.0.0.0 --port "$PORT" --log-level warning &
  SERVER_PID=$!
  SERVER_STARTED=true

  # Wait for server to be ready (up to 15s)
  for i in {1..15}; do
    sleep 1
    if curl -s --max-time 1 "$BASE/health" > /dev/null 2>&1; then
      echo -e "${GREEN}✅ Server ready on port $PORT${NC}"
      break
    fi
    if [ "$i" -eq 15 ]; then
      echo -e "${RED}❌ Server failed to start after 15s${NC}"
      kill $SERVER_PID 2>/dev/null
      exit 1
    fi
  done
else
  echo -e "${GREEN}✅ Server already running${NC}"
fi

echo ""

# ══════════════════════════════════════════════════════════════
# 1. RUNTIME CORRECTNESS — Runs without errors
# ══════════════════════════════════════════════════════════════
hdr "1. RUNTIME CORRECTNESS — Runs without errors"

# Health
HEALTH=$(curl -s "$BASE/health")
if echo "$HEALTH" | grep -q '"healthy"'; then
  ok "/health → {status: healthy}"
else
  fail "/health bad response: $HEALTH"
fi

# OpenAPI docs
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/openapi.json")
[ "$STATUS" = "200" ] && ok "/openapi.json available (HTTP 200)" || fail "/openapi.json HTTP $STATUS"

# Reset doesn't crash
RESET=$(curl -s -X POST "$BASE/reset" 2>&1)
if echo "$RESET" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  ok "/reset returns valid JSON"
else
  fail "/reset error: $RESET"
fi

# Step doesn't crash
STEP=$(curl -s -X POST "$BASE/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type":"classify_ticket","payload":{"classification":"refund"}}' 2>&1)
if echo "$STEP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  ok "/step returns valid JSON"
else
  fail "/step error: $STEP"
fi

# ══════════════════════════════════════════════════════════════
# 2. INTERFACE COMPLIANCE — Follows OpenEnv standard
# ══════════════════════════════════════════════════════════════
hdr "2. INTERFACE COMPLIANCE — Follows OpenEnv standard"

# /metadata
META=$(curl -s "$BASE/metadata")
echo "$META" | grep -q '"name"' && echo "$META" | grep -q '"description"' \
  && ok "/metadata has required fields (name, description)" \
  || fail "/metadata missing fields: $META"

# /schema
SCHEMA=$(curl -s "$BASE/schema")
if echo "$SCHEMA" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'action' in d and 'observation' in d and 'state' in d
" 2>/dev/null; then
  ok "/schema has action + observation + state"
else
  fail "/schema missing required fields: $SCHEMA"
fi

# /reset response shape
RESET=$(curl -s -X POST "$BASE/reset")
if echo "$RESET" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'observation' in d and 'reward' in d and 'done' in d
" 2>/dev/null; then
  ok "/reset response has {observation, reward, done}"
else
  fail "/reset bad shape: $RESET"
fi

# /step response shape
STEP=$(curl -s -X POST "$BASE/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type":"assign_priority","payload":{"priority":"high"}}')
if echo "$STEP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'observation' in d
assert 'reward' in d
assert 'done' in d
r = d['reward']
assert isinstance(r, (int, float)), f'reward must be float, got {type(r)}'
" 2>/dev/null; then
  ok "/step returns {observation, reward(float), done, info}"
else
  fail "/step bad shape or reward not float: $STEP"
fi

# /state response shape
STATE=$(curl -s "$BASE/state")
echo "$STATE" | grep -q '"observation"' && ok "/state returns {observation}" || fail "/state bad shape: $STATE"

# /mcp JSON-RPC
MCP=$(curl -s -X POST "$BASE/mcp" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","id":1}')
echo "$MCP" | grep -q '"jsonrpc"' && ok "/mcp returns JSON-RPC 2.0 response" || fail "/mcp bad response: $MCP"

# ══════════════════════════════════════════════════════════════
# 3. TASK DESIGN — Clear, realistic, testable
# ══════════════════════════════════════════════════════════════
hdr "3. TASK DESIGN — Clear, realistic, testable"

TASKS=$(curl -s "$BASE/tasks")
TASK_COUNT=$(echo "$TASKS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)
GRADED_COUNT=$(echo "$TASKS" | python3 -c "import sys,json; t=json.load(sys.stdin); print(sum(1 for x in t if x.get('grader')))" 2>/dev/null)

info "Total tasks: $TASK_COUNT | Tasks with graders: $GRADED_COUNT"

[ "${TASK_COUNT:-0}" -ge 3 ] \
  && ok "≥3 tasks defined (found $TASK_COUNT)" \
  || fail "Need ≥3 tasks, found ${TASK_COUNT:-0}"

[ "${GRADED_COUNT:-0}" -ge 3 ] \
  && ok "≥3 tasks have grader=true (found $GRADED_COUNT)" \
  || fail "Need ≥3 graded tasks, found ${GRADED_COUNT:-0}"

# Check tasks have required design fields
DESIGN_OK=$(echo "$TASKS" | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
required = ['id','name','difficulty','objective','description']
missing = []
for t in tasks:
    for f in required:
        if f not in t:
            missing.append(f'{t.get(\"id\",\"?\")}:{f}')
print(len(missing))
" 2>/dev/null)
[ "${DESIGN_OK:-1}" -eq 0 ] \
  && ok "All tasks have required design fields (id, name, difficulty, objective, description)" \
  || fail "Some tasks missing design fields: $DESIGN_OK"

# Check difficulty spread
DIFF_SPREAD=$(echo "$TASKS" | python3 -c "
import sys,json
t = json.load(sys.stdin)
diffs = set(x.get('difficulty','') for x in t)
print('ok' if len(diffs) >= 2 else 'fail')
" 2>/dev/null)
[ "$DIFF_SPREAD" = "ok" ] \
  && ok "Tasks span multiple difficulty levels (EASY / MEDIUM / HARD)" \
  || fail "All tasks same difficulty — needs spread"

# ══════════════════════════════════════════════════════════════
# 4. GRADING LOGIC — Reward system makes sense
# ══════════════════════════════════════════════════════════════
hdr "4. GRADING LOGIC — Reward system in [0.0, 1.0]"

TASK_IDS=$(echo "$TASKS" | python3 -c "
import sys,json
t=json.load(sys.stdin)
for x in t:
    if x.get('grader'): print(x['id'])
" 2>/dev/null)

GRADER_OK=0
GRADER_FAIL=0
for TID in $TASK_IDS; do
  RESULT=$(curl -s "$BASE/grader?task_id=$TID")
  CHECK=$(echo "$RESULT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=float(d.get('score','-1'))
if 0.0 <= s <= 1.0:
    print(f'ok:{s}')
else:
    print(f'fail:{s}')
" 2>/dev/null)
  if echo "$CHECK" | grep -q "^ok:"; then
    SCORE=$(echo "$CHECK" | cut -d: -f2)
    info "$TID → score=$SCORE ✅"
    ((GRADER_OK++))
  else
    info "$TID → grader error or out-of-range: $RESULT"
    ((GRADER_FAIL++))
  fi
done

[ "$GRADER_OK" -ge 3 ] \
  && ok "$GRADER_OK graders return valid scores in [0.0, 1.0]" \
  || fail "Only $GRADER_OK graders valid — need ≥3"

# ══════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════"
echo -e "  Results: ${GREEN}$PASS passed${NC}  |  ${RED}$FAIL failed${NC}"
echo "══════════════════════════════════════════════════════════"
echo ""

# Cleanup server if we started it
if [ "$SERVER_STARTED" = true ] && [ -n "$SERVER_PID" ]; then
  kill $SERVER_PID 2>/dev/null
  echo "Server stopped."
fi

if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}🎉 ALL CHECKS PASSED — Ready for OpenEnv submission!${NC}"
  exit 0
else
  echo -e "${RED}❌ $FAIL check(s) failed — Fix before submitting.${NC}"
  exit 1
fi
