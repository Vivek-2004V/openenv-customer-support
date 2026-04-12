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
info() { echo -e "  ${YELLOW}ℹ️   ${NC}$1"; }
hdr()  { echo -e "\n${BLUE}▶ $1${NC}"; }

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║    OpenEnv Customer Support — Submission Validator   ║"
echo "╚══════════════════════════════════════════════════════╝"

# ── Always use .venv python ────────────────────────────────────
VENV_PYTHON=".venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
  echo -e "${RED}❌ .venv not found. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt${NC}"
  exit 1
fi

# Use venv python for all inline python calls in this script
PY="$VENV_PYTHON"

# ── Auto-start server if not running ──────────────────────────
echo ""
echo "Checking server at $BASE ..."
if ! curl -s --max-time 2 "$BASE/health" > /dev/null 2>&1; then
  echo -e "${YELLOW}⚡ Server not running — starting on port $PORT ...${NC}"

  # Verify imports before starting
  if ! $PY -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing dependencies ...${NC}"
    $PY -m pip install -q -r requirements.txt
  fi

  # Start server in background using .venv
  $PY -m uvicorn server.app:app --host 0.0.0.0 --port "$PORT" --log-level warning &
  SERVER_PID=$!
  SERVER_STARTED=true

  # Wait up to 20s for server to be ready
  READY=false
  for i in $(seq 1 20); do
    sleep 1
    if curl -s --max-time 1 "$BASE/health" > /dev/null 2>&1; then
      READY=true
      echo -e "${GREEN}✅ Server ready (took ${i}s)${NC}"
      break
    fi
  done

  if [ "$READY" = false ]; then
    echo -e "${RED}❌ Server failed to start after 20s${NC}"
    echo "   Check: cd openenv-customer-support && .venv/bin/python -m uvicorn server.app:app --port $PORT"
    kill $SERVER_PID 2>/dev/null
    exit 1
  fi
else
  echo -e "${GREEN}✅ Server already running on port $PORT${NC}"
fi

echo ""

# ══════════════════════════════════════════════════════════════
# 1. RUNTIME CORRECTNESS — Runs without errors
# ══════════════════════════════════════════════════════════════
hdr "1. RUNTIME CORRECTNESS — Runs without errors"

# /health
HEALTH=$(curl -s --max-time 5 "$BASE/health" 2>/dev/null)
if echo "$HEALTH" | grep -q '"healthy"'; then
  ok "/health returns {status: healthy}"
else
  fail "/health bad response: ${HEALTH:-no response}"
fi

# /openapi.json
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE/openapi.json" 2>/dev/null)
[ "$STATUS" = "200" ] && ok "/openapi.json available (HTTP 200)" || fail "/openapi.json HTTP ${STATUS:-timeout}"

# /reset doesn't crash
RESET=$(curl -s --max-time 10 -X POST "$BASE/reset" 2>/dev/null)
if echo "$RESET" | $PY -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  ok "/reset returns valid JSON without crashing"
else
  fail "/reset crashed or invalid: ${RESET:-no response}"
fi

# /step doesn't crash
STEP=$(curl -s --max-time 10 -X POST "$BASE/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type":"classify_ticket","payload":{"classification":"refund"}}' 2>/dev/null)
if echo "$STEP" | $PY -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  ok "/step returns valid JSON without crashing"
else
  fail "/step crashed or invalid: ${STEP:-no response}"
fi

# ══════════════════════════════════════════════════════════════
# 2. INTERFACE COMPLIANCE — Follows OpenEnv standard
# ══════════════════════════════════════════════════════════════
hdr "2. INTERFACE COMPLIANCE — Follows OpenEnv standard"

# /metadata
META=$(curl -s --max-time 5 "$BASE/metadata" 2>/dev/null)
if echo "$META" | grep -q '"name"' && echo "$META" | grep -q '"description"'; then
  ok "/metadata has required fields (name, description)"
else
  fail "/metadata missing fields: ${META:-no response}"
fi

# /schema
SCHEMA=$(curl -s --max-time 5 "$BASE/schema" 2>/dev/null)
if echo "$SCHEMA" | $PY -c "
import sys,json
d=json.load(sys.stdin)
assert 'action' in d and 'observation' in d and 'state' in d
" 2>/dev/null; then
  ok "/schema has action + observation + state"
else
  fail "/schema missing required fields: ${SCHEMA:-no response}"
fi

# /reset response shape: {observation, reward, done}
RESET=$(curl -s --max-time 10 -X POST "$BASE/reset" 2>/dev/null)
if echo "$RESET" | $PY -c "
import sys,json
d=json.load(sys.stdin)
assert 'observation' in d and 'reward' in d and 'done' in d
" 2>/dev/null; then
  ok "/reset response has {observation, reward, done}"
else
  fail "/reset bad shape: ${RESET:-no response}"
fi

# /step response shape: {observation, reward(float), done, info}
STEP=$(curl -s --max-time 10 -X POST "$BASE/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type":"assign_priority","payload":{"priority":"high"}}' 2>/dev/null)
if echo "$STEP" | $PY -c "
import sys,json
d=json.load(sys.stdin)
assert 'observation' in d and 'reward' in d and 'done' in d
assert isinstance(d['reward'], (int,float))
" 2>/dev/null; then
  ok "/step returns {observation, reward(float), done, info}"
else
  fail "/step bad response shape: ${STEP:-no response}"
fi

# /state
STATE=$(curl -s --max-time 5 "$BASE/state" 2>/dev/null)
if echo "$STATE" | grep -q '"observation"'; then
  ok "/state returns {observation}"
else
  fail "/state bad shape: ${STATE:-no response}"
fi

# /mcp JSON-RPC 2.0
MCP=$(curl -s --max-time 5 -X POST "$BASE/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}' 2>/dev/null)
if echo "$MCP" | grep -q '"jsonrpc"'; then
  ok "/mcp returns JSON-RPC 2.0 response"
else
  fail "/mcp bad response: ${MCP:-no response}"
fi

# ══════════════════════════════════════════════════════════════
# 3. TASK DESIGN — Clear, realistic, testable
# ══════════════════════════════════════════════════════════════
hdr "3. TASK DESIGN — Clear, realistic, testable"

TASKS_JSON=$(curl -s --max-time 10 "$BASE/tasks" 2>/dev/null)

TASK_COUNT=$( echo "$TASKS_JSON" | $PY -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null )
GRADED_COUNT=$(echo "$TASKS_JSON" | $PY -c "import sys,json; t=json.load(sys.stdin); print(sum(1 for x in t if x.get('grader')))" 2>/dev/null)

info "Total tasks: ${TASK_COUNT:-?} | With graders: ${GRADED_COUNT:-?}"

[ "${TASK_COUNT:-0}" -ge 3 ]   && ok "≥3 tasks defined (found $TASK_COUNT)"          || fail "Need ≥3 tasks, found ${TASK_COUNT:-0}"
[ "${GRADED_COUNT:-0}" -ge 3 ] && ok "≥3 tasks have grader=true (found $GRADED_COUNT)" || fail "Need ≥3 graded tasks, found ${GRADED_COUNT:-0}"

# Required design fields
DESIGN_ISSUES=$(echo "$TASKS_JSON" | $PY -c "
import sys,json
tasks=json.load(sys.stdin)
required=['id','name','difficulty','objective','description']
missing=[]
for t in tasks:
    for f in required:
        if f not in t:
            missing.append(f'{t.get(\"id\",\"?\")}:{f}')
print(len(missing))
" 2>/dev/null)
[ "${DESIGN_ISSUES:-1}" -eq 0 ] \
  && ok "All tasks have required fields (id, name, difficulty, objective, description)" \
  || fail "Some tasks missing design fields (${DESIGN_ISSUES} issues)"

# Difficulty spread
DIFF_OK=$(echo "$TASKS_JSON" | $PY -c "
import sys,json
t=json.load(sys.stdin)
diffs=set(x.get('difficulty','') for x in t)
print('ok' if len(diffs)>=2 else 'fail')
" 2>/dev/null)
[ "$DIFF_OK" = "ok" ] && ok "Tasks span multiple difficulty levels" || fail "All tasks same difficulty — need spread"

# ══════════════════════════════════════════════════════════════
# 4. GRADING LOGIC — Reward system in [0.0, 1.0]
# ══════════════════════════════════════════════════════════════
hdr "4. GRADING LOGIC — Reward system in [0.0, 1.0]"

TASK_IDS=$(echo "$TASKS_JSON" | $PY -c "
import sys,json
for x in json.load(sys.stdin):
    if x.get('grader'): print(x['id'])
" 2>/dev/null)

GRADER_OK=0
GRADER_FAIL=0
for TID in $TASK_IDS; do
  RESULT=$(curl -s --max-time 10 "$BASE/grader?task_id=$TID" 2>/dev/null)
  SCORE_CHECK=$(echo "$RESULT" | $PY -c "
import sys,json
d=json.load(sys.stdin)
s=float(d.get('score',-1))
print('ok' if 0.0<=s<=1.0 else 'fail', s)
" 2>/dev/null)
  if echo "$SCORE_CHECK" | grep -q "^ok"; then
    SCORE=$(echo "$SCORE_CHECK" | awk '{print $2}')
    info "$TID → score=$SCORE ✅"
    ((GRADER_OK++))
  else
    info "$TID → ERROR: ${RESULT:-no response}"
    ((GRADER_FAIL++))
  fi
done

[ "$GRADER_OK" -ge 3 ] \
  && ok "$GRADER_OK/$(echo $TASK_IDS | wc -w | tr -d ' ') graders return valid scores in [0.0, 1.0]" \
  || fail "Only $GRADER_OK valid graders — need ≥3"

# ══════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════"
echo -e "  Results: ${GREEN}${PASS} passed${NC}  |  ${RED}${FAIL} failed${NC}"
echo "══════════════════════════════════════════════════════════"
echo ""

# Stop server if we started it
if [ "$SERVER_STARTED" = true ] && [ -n "$SERVER_PID" ]; then
  kill $SERVER_PID 2>/dev/null
  echo "Server stopped."
fi

if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}🎉 ALL CHECKS PASSED — Ready for OpenEnv submission!${NC}"
  exit 0
else
  echo -e "${RED}❌ ${FAIL} check(s) failed — Fix before submitting.${NC}"
  exit 1
fi
