#!/usr/bin/env python3
"""从 DealCloud / SharePoint 等 MCP 系统拉取对账所需的真实记录级数据。"""
import sys, json
sys.path.insert(0, "/home/lab434/rl-lab/mimo-docker")
from rollout2 import load_instance, mcp_servers, bridge

iid = "s3k_0000_accounting_audit_tax_en_t1_rl_008"
info = load_instance(iid)
servers = dict(mcp_servers(info["task_dir"]))
DC = servers["dealcloud_disposition_workspace"]
SP = servers.get("sharepoint_tax_governance_library")
CASE = "CASE-FAIRFAX3-2025Q3"


def call(url, name, tool, args, limit=3000):
    r = bridge(None, url, name, {"tool": tool, "arguments": args})
    print(f"### {name}::{tool} {json.dumps(args, ensure_ascii=False)}")
    print(json.dumps(r, ensure_ascii=False, indent=1)[:limit])
    print()
    return r


def list_tools(url, name):
    r = bridge(None, url, name, None)
    items = r.get("tools") or (r.get("result") or {}).get("tools") or []
    print(f"=== {name}: {len(items)} tools")
    for t in items:
        print("  -", t.get("name"), "|", (t.get("description") or "")[:100])
    print()
    return [t.get("name") for t in items]


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "sp"):
        list_tools(SP, "sharepoint")
    if which in ("all", "dc"):
        list_tools(DC, "dealcloud")
        call(DC, "dealcloud", "search_disposition_transactions", {"page_size": 50})
        call(DC, "dealcloud", "get_withholding_and_closing_status",
             {"case_id": CASE, "active_only": False})
        call(DC, "dealcloud", "recompute_documentary_transfer_tax", {"case_id": CASE})
