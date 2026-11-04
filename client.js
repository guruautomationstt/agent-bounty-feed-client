#!/usr/bin/env node
/**
 * Agent Bounty Feed — Minimal Zero-Dependency MCP & x402 Client
 * Repository: https://github.com/ami-guru/agent-bounty-feed-client
 * 
 * Works in Node.js 18+ with zero npm dependencies.
 */

const MCP_ENDPOINT = 'https://agent-bounty-feed.dailydollar.workers.dev/mcp';

async function queryMcp(toolName, args = {}) {
  // Step 1: Initialize MCP session (Streamable HTTP)
  const initRes = await fetch(MCP_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'agent-bounty-feed-client', version: '1.0.0' }
      }
    })
  });

  if (!initRes.ok) {
    throw new Error(`MCP initialization failed: ${initRes.status} ${initRes.statusText}`);
  }

  const sessionId = initRes.headers.get('mcp-session-id');
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream'
  };
  if (sessionId) headers['mcp-session-id'] = sessionId;

  // Step 2: Call tool (tools/call)
  const toolRes = await fetch(MCP_ENDPOINT, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args
      }
    })
  });

  if (!toolRes.ok) {
    throw new Error(`Tool call failed: ${toolRes.status} ${toolRes.statusText}`);
  }

  const toolData = await toolRes.json();
  if (toolData.error) {
    throw new Error(`MCP Tool Error: ${toolData.error.message}`);
  }
  
  const text = toolData.result?.content?.[0]?.text;
  return text ? JSON.parse(text) : toolData.result;
}

async function main() {
  console.log('===============================================================');
  console.log('🤖 Agent Bounty Feed (ABF) — Minimal Streamable HTTP MCP Client');
  console.log('   Endpoint: https://agent-bounty-feed.dailydollar.workers.dev/mcp');
  console.log('===============================================================\n');

  try {
    console.log('[*] Querying open claimable bounties (filtering: no KYC, no stake, no bond)...');
    const data = await queryMcp('list_bounties', {
      exclude_requires: 'kyc,stake,bond',
      limit: 15,
      sort: 'reward'
    });

    const items = data.items || [];
    console.log(`[+] Discovered ${items.length} claimable bounties:\n`);

    items.forEach((item, idx) => {
      const reward = `${item.reward} ${item.currency || 'USD'}`;
      const network = item.network ? `(${item.network})` : '';
      const deadline = item.deadline ? `[Deadline: ${item.deadline.slice(0, 10)}]` : '[No deadline]';
      
      console.log(`${(idx + 1).toString().padStart(2, ' ')}. [${reward.padEnd(10)}] ${network.padEnd(14)} ${item.title}`);
      console.log(`    ID:       ${item.id}`);
      console.log(`    URL:      ${item.url}`);
      console.log(`    Requires: ${(item.requires || []).join(', ') || 'none'}`);
      console.log(`    Notice:   ${deadline} ${(item.eligibility || '').slice(0, 95)}...\n`);
    });

    console.log('---------------------------------------------------------------');
    console.log('✔ Verification successful. Zero external dependencies.');
    console.log('✔ Run anytime with: node client.js');
    console.log('===============================================================');
  } catch (err) {
    console.error('[-] Error executing client:', err.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
