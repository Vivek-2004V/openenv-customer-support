#!/usr/bin/env bash
# ============================================================
# OpenEnv Submission Validator
# Tests all 4 evaluation criteria locally before submission
# Usage: bash scripts/validate-submission.sh
# ============================================================

set -e
BASE="http://localhost:7860"
PASS=0
FAIL=0
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✅ PASS${NC} — $1"; ((PASS++)); }
fail() { echo -e "  ${RED}❌ FAIL${NC} — $1"; ((FAIL++)); }
info() { echo -e "  ${YELLOW}ℹ️  ${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║    OpenEnv Customer Support — Submission Validator   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. Runtime Correctness ──────────────────────────────────
echo "▶ 1. RUNTIME CORRECTNESS — Runs without errors"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/health")
if [ "$STATUS" = "200" ]; then
  HEALTH=$(curl -s "$BASE/health")
  if echo "$HEALTH" | grep -q '"healthy"'; then
    ok "/health returns {status: healthy} (HTTP 200)"
  else
    fail "/health response missing 'healthy': $HEALTH"
  fi
else
  fail "/health endpoint unreachable (HTTP $STATUS)"
fi

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/openapi.json")
[ "$STATUS" = "200" ] && ok "/openapi.json reachable (HTTP 200)" || fail "/openapi.json not found"

echo ""

# ── 2. Interface Compliance ─────────────────────────────────
echo "▶ 2. INTERFACE COMPLIANCE — Follows OpenEnv standard"

# /metadata
META=$(curl -s "$BASE/metadata")
echo "$META" | grep -q '"name"' && echo "$META" | grep -q '"description"' \
  && ok "/metadata has name + description" \
  || fail "/metadata missing required fields: $META"

# /schema
SCHEMA=$(curl -s "$BASE/schema")
echo "$SCHEMA" | grep -q '"action"' && echo "$SCHEMA" | grep -q '"observation"' && echo "$SCHEMA" | grep -q '"state"' \
  && ok "/schema has action + observation + state" \
  || fail "/schema missing required fields"

# /reset
RESET=$(curl -s -X POST "$BASE/reset")
echo "$RESET" | grep -q '"observation"' \
  && ok "/reset returns observation" \
  || fail "/reset bad response: $RESET"

# /step
STEP=$(curl -s -X POST "$BASE/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type":"classify_ticket","payload":{"classification":"refund"}}')
echo "$STEP" | grep -q '"observation"' && echo "$STEP" | grep -q '"reward"' && echo "$STEP" | grep -q '"done"' \
  && ok "/step returns observation + reward + done" \
  || fail "/step bad response: $STEP"

# /state
STATE=$(curl -s "$BASE/state")
echo "$STATE" | grep -q '"observation"' \
  && ok "/state returns observation" \
  || fail "/state bad response: $STATE"

echo ""

# ── 3. Task Design ──────────────────────────────────────────
echo "▶ 3. TASK DESIGN — Clear, realistic, testable"

TASKS=$(curl -s "$BASE/tasks")
TASK_COUNT=$(echo "$TASKS" | python3 -c "import sys,json; t=json.load(sys.stdin); print(len(t))" 2>/dev/null)
GRADED_COUNT=$(echo "$TASKS" | python3 -c "import sys,json; t=json.load(sys.stdin); print(sum(1 for x in t if x.get('grader')))" 2>/dev/null)

info "Found $TASK_COUNT tasks, $GRADED_COUNT with graders"
[ "$TASK_COUNT" -ge 3 ] && ok "At least 3 tasks defined" || fail "Need ≥3 tasks, found $TASK_COUNT"
[ "$GRADED_COUNT" -ge 3 ] && ok "At least 3 tasks have graders" || fail "Need ≥3 tasks with graders, found $GRADED_COUNT"

echo ""

# ── 4. Grading Logic ────────────────────────────────────────
echo "▶ 4. GRADING LOGIC — Reward system makes sense"

TASK_IDS=$(echo "$TASKS" | python3 -c "import sys,json; t=json.load(sys.stdin); [print(x['id']) for x in t if x.get('grader')]" 2>/dev/null)

GRADER_OK=0
GRADER_FAIL=0
for TID in $TASK_IDS; do
  RESULT=$(curl -s "$BASE/grader?task_id=$TID")
  SCORE=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('score',''))" 2>/dev/null)
  if [ -n "$SCORE" ]; then
    IN_RANGE=$(python3 -c "s=float('$SCORE'); print('ok' if 0.0<=s<=1.0 else 'fail')" 2>/dev/null)
    if [ "$IN_RANGE" = "ok" ]; then
      info "$TID → score=$SCORE ✅"
      ((GRADER_OK++))
    else
      info "$TID → score=$SCORE ❌ (out of range)"
      ((GRADER_FAIL++))
    fi
  else
    info "$TID → grader error: $RESULT"
    ((GRADER_FAIL++))
  fi
done

[ "$GRADER_OK" -ge 3 ] && ok "$GRADER_OK graders return valid scores in [0.0, 1.0]" \
  || fail "Only $GRADER_OK graders valid, need ≥3"

echo ""
echo "══════════════════════════════════════════════════════"
echo -e "  Results: ${GREEN}$PASS passed${NC}  |  ${RED}$FAIL failed${NC}"
echo "══════════════════════════════════════════════════════"
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}🎉 ALL CHECKS PASSED — Ready for OpenEnv submission!${NC}"
  exit 0
else
  echo -e "${RED}❌ $FAIL check(s) failed — Fix before submitting.${NC}"
  exit 1
fi
