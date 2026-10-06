#!/bin/bash
# MiMo-V2.6-RL-oss 长程批量实验
# 预计运行时间: 6小时
# 输出: /home/lab434/research/rl-lab/mimo-docker/out/

set -e
cd /home/lab434/research/rl-lab/mimo-docker

# 实验配置
INSTANCES=(
  "s3k_0000_accounting_audit_tax_en_t1_rl_008"
  "s3k_0001_accounting_audit_tax_en_t1_rl_002"
  "s3k_0001_accounting_audit_tax_en_t1_rl_003"
  "s3k_0004_accounting_audit_tax_en_t1_rl_001"
  "s3k_0010_accounting_audit_tax_en_t1_rl_001"
  "s3k_0013_accounting_audit_tax_en_t1_rl_001"
)

MODEL="MiniMax-M3"
MAX_STEPS=60
ROLLOUT_TIMEOUT=1800

export GA_JUDGE_URL="https://api.minimaxi.com/v1"
export GA_JUDGE_KEY="$(cat /home/lab434/.openclaw/secrets/minimax.key)"
export GA_JUDGE_MODEL="MiniMax-M3"
export GA_JUDGE_API="chat"
export VERIFY_DETERMINISTIC="1"
export VERIFY_AGENT_JUDGE="1"

echo "[batch] start time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "[batch] instances: ${#INSTANCES[@]}"
echo "[batch] model: $MODEL"

PASS=0
FAIL=0

for IID in "${INSTANCES[@]}"; do
  echo ""
  echo "========================================"  | tee -a /tmp/mimo-batch.log
  echo "[batch] instance=$IID"
  echo "[batch] start: $(date '+%H:%M:%S')" | tee -a /tmp/mimo-batch.log
  
  # 1. up
  echo "[batch] step 1: up" | tee -a /tmp/mimo-batch.log
  python3 mimo_env_runner.py up --instance "$IID" >> /tmp/mimo-batch.log 2>&1
  
  # 2. rollout
  echo "[batch] step 2: rollout (max $MAX_STEPS steps)" | tee -a /tmp/mimo-batch.log
  python3 rollout2.py --instance "$IID" --max-steps $MAX_STEPS --model "$MODEL" \
    >> /tmp/mimo-batch.log 2>&1 || true
  
  # 3. verify
  echo "[batch] step 3: verify" | tee -a /tmp/mimo-batch.log
  python3 mimo_env_runner.py verify --instance "$IID" >> /tmp/mimo-batch.log 2>&1 || true
  
  # 4. 检查 reward
  REWARD_FILE="out/$IID/reward.json"
  if [ -f "$REWARD_FILE" ]; then
    REWARD=$(python3 -c "import json; print(json.load(open('$REWARD_FILE')).get('reward'))")
    echo "[batch] reward=$REWARD" | tee -a /tmp/mimo-batch.log
    if [ "$REWARD" == "1.0" ]; then
      PASS=$((PASS+1))
    else
      FAIL=$((FAIL+1))
    fi
  else
    echo "[batch] reward=missing" | tee -a /tmp/mimo-batch.log
    FAIL=$((FAIL+1))
  fi
  
  # 5. down
  echo "[batch] step 4: down" | tee -a /tmp/mimo-batch.log
  python3 mimo_env_runner.py down --instance "$IID" >> /tmp/mimo-batch.log 2>&1 || true
  
  echo "[batch] end: $(date '+%H:%M:%S')" | tee -a /tmp/mimo-batch.log
done

echo ""
echo "========================================"  | tee -a /tmp/mimo-batch.log
echo "[batch] COMPLETE"
echo "[batch] pass=$PASS fail=$FAIL total=${#INSTANCES[@]}"
echo "[batch] end time: $(date '+%Y-%m-%d %H:%M:%S %Z')" | tee -a /tmp/mimo-batch.log
