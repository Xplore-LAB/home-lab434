#!/usr/bin/env python3
"""按交易 ID 逐笔拉 DealCloud 明细 + SharePoint 决策记录。"""
import sys, json
sys.path.insert(0, "/home/lab434/rl-lab/mimo-docker")
from rollout2 import load_instance, mcp_servers, bridge

iid = "s3k_0000_accounting_audit_tax_en_t1_rl_008"
info = load_instance(iid)
servers = dict(mcp_servers(info["task_dir"]))
DC = servers["dealcloud_disposition_workspace"]
SP = servers["sharepoint_tax_governance_library"]
CASE = "CASE-FAIRFAX3-2025Q3"


def call(url, name, tool, args, limit=2600):
    r = bridge(None, url, name, {"tool": tool, "arguments": args})
    print(f"### {name}::{tool} {json.dumps(args, ensure_ascii=False)}")
    txt = json.dumps(r, ensure_ascii=False, indent=1)
    print(txt[:limit])
    print()
    return r


TXN = "DC-TXN-25Q3-024"
for t in ("DC-TXN-25Q3-017", "DC-TXN-25Q3-021", TXN):
    call(DC, "dealcloud", "get_withholding_and_closing_status",
         {"case_id": CASE, "transaction_id": t, "active_only": True}, 2200)
    call(DC, "dealcloud", "get_transfer_tax_requirements",
         {"transaction_id": t, "include_inactive": True}, 2000)
    call(DC, "dealcloud", "get_consideration_terms", {"transaction_id": t}, 1500)

call(DC, "dealcloud", "search_disposition_transactions",
     {"transaction_status": "recommended", "page_size": 10}, 1500)
call(SP, "sharepoint", "get_decision_record", {"decision_id": "DEC-2025-017"}, 1800)
call(SP, "sharepoint", "get_decision_record", {"case_id": CASE}, 1800)
call(SP, "sharepoint", "check_document_lineage", {"case_id": CASE}, 1500)
