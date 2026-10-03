// Copyright 2026 Edward Rajah
// SPDX-License-Identifier: Apache-2.0

/**
 * The guard rules, in one place so the landing page and the docs cannot drift
 * apart. Sourced from plugins/browser-guard.ts and docs/AGENTS.fragment.md.
 */
export interface GuardRule {
  id: string
  verdict: 'allow' | 'deny'
  call: string
  rule: string
  why: string
}

export const GUARDS: GuardRule[] = [
  {
    id: 'browser-close',
    verdict: 'deny',
    call: 'browser_close',
    rule: 'Always denied',
    why: 'Tears down the shared browser. Every other instance attached to it loses their tabs mid-task, and there is no way to tell how much work that was.',
  },
  {
    id: 'last-tab',
    verdict: 'deny',
    call: 'browser_tabs close',
    rule: 'Never the last tab',
    why: 'The same failure by another route. Closing the final page makes the browser exit, so the guard refuses any index that resolves to it.',
  },
  {
    id: 'explicit-index',
    verdict: 'deny',
    call: 'browser_tabs close',
    rule: 'Explicit index required',
    why: 'A bare close carries no intent. Without an index the guard cannot reason about which tab would go, so it declines rather than guess.',
  },
  {
    id: 'foreign-tab',
    verdict: 'deny',
    call: 'browser_tabs close',
    rule: 'Denied while any foreign tab exists',
    why: 'The MCP tab index does not map onto a CDP target, and close accepts no target ID — so ownership of one specific tab is unverifiable. Closing is allowed only when every live tab is claimed by this session or inert.',
  },
  {
    id: 'ttl-expiry',
    verdict: 'allow',
    call: 'tool.execute.before',
    rule: 'Claims expire after 15 min',
    why: 'Ownership lives only in the agent process. A stale claim from a finished instance would otherwise block closes forever, so it ages out and the tab counts as unowned again.',
  },
  {
    id: 'inert-tabs',
    verdict: 'allow',
    call: 'browser_tabs close',
    rule: 'Blank tabs are ignored',
    why: 'The browser always keeps one seed about:blank that no session claims. Treating it as foreign would deny every close permanently.',
  },
  {
    id: 'fail-closed',
    verdict: 'deny',
    call: 'browser_tabs close',
    rule: 'Fails closed',
    why: 'If CDP cannot be reached, live tabs cannot be enumerated, so no close can be verified. Unverifiable means denied.',
  },
  {
    id: 'own-tab',
    verdict: 'allow',
    call: 'browser_tabs close',
    rule: 'Own tabs are closable',
    why: 'When every live tab belongs to this session, whichever one the index resolves to is ours by definition.',
  },
]