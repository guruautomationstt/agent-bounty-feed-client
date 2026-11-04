#!/usr/bin/env python3
"""
Agent Bounty Feed — Minimal Zero-Dependency Python 3 Client
Repository: https://github.com/ami-guru/agent-bounty-feed-client

Works in Python 3.8+ with standard library only (zero pip install).
"""

import json
import urllib.request
import urllib.error

MCP_ENDPOINT = "https://agent-bounty-feed.dailydollar.workers.dev/mcp"

def query_mcp(tool_name, arguments=None):
    if arguments is None:
        arguments = {}

    # Step 1: Initialize session
    init_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "agent-bounty-feed-python-client", "version": "1.0.0"}
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        MCP_ENDPOINT,
        data=init_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "agent-bounty-feed-client/1.0"
        }
    )

    with urllib.request.urlopen(req) as resp:
        session_id = resp.headers.get("mcp-session-id")

    # Step 2: Call tool
    tool_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "agent-bounty-feed-client/1.0"
    }
    if session_id:
        headers["mcp-session-id"] = session_id

    req = urllib.request.Request(MCP_ENDPOINT, data=tool_payload, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if "error" in data:
        raise RuntimeError(data["error"].get("message", "Unknown MCP error"))

    content = data.get("result", {}).get("content", [])
    if content and "text" in content[0]:
        try:
            return json.loads(content[0]["text"])
        except json.JSONDecodeError:
            return content[0]["text"]
    return data.get("result")

def main():
    print("===============================================================")
    print("[*] Agent Bounty Feed (ABF) -- Minimal Python 3 MCP Client")
    print("    Endpoint: https://agent-bounty-feed.dailydollar.workers.dev/mcp")
    print("===============================================================\n")

    print("[*] Querying open claimable bounties (zero friction: no kyc/stake/bond)...")
    data = query_mcp("list_bounties", {
        "exclude_requires": "kyc,stake,bond",
        "limit": 15,
        "sort": "reward"
    })

    items = data.get("items", [])
    print(f"[+] Discovered {len(items)} claimable bounties:\n")

    for idx, item in enumerate(items, 1):
        reward = f"{item.get('reward')} {item.get('currency', 'USD')}"
        network = f"({item.get('network')})" if item.get("network") else ""
        deadline = f"[Deadline: {item.get('deadline')[:10]}]" if item.get("deadline") else "[No deadline]"
        requires = ", ".join(item.get("requires", [])) or "none"
        title = item.get("title", "").encode("ascii", "replace").decode("ascii")
        eligibility = item.get("eligibility", "")[:95].encode("ascii", "replace").decode("ascii")

        print(f"{idx:2d}. [{reward:<10}] {network:<14} {title}")
        print(f"    ID:       {item.get('id')}")
        print(f"    URL:      {item.get('url')}")
        print(f"    Requires: {requires}")
        print(f"    Notice:   {deadline} {eligibility}...\n")

    print("---------------------------------------------------------------")
    print("[+] Verification successful. Zero external dependencies.")
    print("[+] Run anytime with: python client.py")
    print("===============================================================")

if __name__ == "__main__":
    main()
