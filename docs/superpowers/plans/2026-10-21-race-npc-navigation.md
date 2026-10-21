# Race NPC Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop Original from spinning or targeting unreachable noodle bowls in After the Rain, and provide Normal plus a fully local strategic Hard mode.

**Architecture:** Build a local graph from valid walkable samples and use A* paths for reachable bowls and waypoint movement. Normal uses deterministic local scoring. Hard uses bounded two-bowl lookahead and makes Original react faster while preserving standard player speed and Original's maximum speed. All race logic stays local.

**Tech Stack:** Existing Three.js in `game.html` and local route scoring.

**Spec:** `docs/superpowers/specs/2026-10-21-race-npc-navigation-design.md`

## Global Constraints

- Both race modes run without network or external AI requests. Chatbot AI remains a separate feature.
- Character movement, yaw, collision, stamina, and waypoint following run locally each frame.
- In Hard, keep player speeds unchanged; increase Original's turn response, acceleration, sprint anticipation, and route recovery response without raising its maximum speed.
- Do not add or run automated tests in this task; use code inspection, syntax parsing, and diff checks only.

## Review Focus

- A sampled floor node with no valid edge must not create a fake route; inspect edge acceptance and path reconstruction in Task 1.
- A destination behind a wall or on a disconnected floor region must be excluded from NPC target choices; inspect candidate path cost in Task 2.
- A graph edge that fails during movement must lead to bounded replanning/backtracking rather than rotation; inspect progress state and retry caps in Task 2.
- Hard's lookahead must use only currently reachable, uncollected bowl candidates and keep pathfinding bounded; inspect the candidate shortlist and second-leg scoring in Task 4.
- Hard response tuning must apply only during an active Hard race; verify Normal and non-race NPC movement remain unchanged and player speeds stay standard in both modes.

---

### Task 1: Build the race walkable graph and A* path interface

**Files:**
- Modify: `game.html` near `findWalkables()` and race helper functions around `chooseRaceBowl()`.

**Interfaces:**
- Produces: `buildRaceGraph(points, gridStep) -> RaceGraph`, where each node contains `id`, `{x,y,z}`, and an adjacency list of `{to, distance, clearance, cost}`.
- Produces: `nearestRaceNode(graph, x, y, z) -> nodeId | null`.
- Produces: `findRacePath(graph, startId, goalId, blockedEdges) -> { nodes: number[], cost: number } | null`.
- Consumes: current walkable candidate array, grid spacing computed from current map bounds, `cast`, `groundAt`, `npcWallAhead`, and map collision geometry.

- [x] **Step 1: Inspect graph candidates and compare each prospective neighbor edge against current NPC wall, step-up (`NPC_CFG.stepUp`), and drop (`NPC_CFG.drop`) checks.** Record that invalid or disconnected neighbors never become edges.
- [x] **Step 2: Add `buildRaceGraph(points, gridStep)` to connect candidate points in adjacent spatial hash cells with valid floor continuity and open width; assign distance cost at least equal to edge distance with a modest preference for wider, higher-connectivity corridors.** Keep the graph local to the active map and avoid an all-pairs node scan.
- [x] **Step 3: Add `nearestRaceNode()` and `findRacePath()` using A* with a Euclidean heuristic and an optional temporary blocked-edge set.** Return `null` when no path exists and reconstruct a path with its exact graph node IDs and accumulated cost.
- [x] **Step 4: Inspect path reconstruction and edge filters for disconnected components, start equal to goal, and blocked final edges.** Confirm the returned nodes are adjacent in the graph and the reported cost is finite.
- [x] **Step 5: Run JavaScript syntax parsing on the inline game script and `git diff --check`.**

### Task 2: Make Normal race target selection and NPC movement follow the graph

**Files:**
- Modify: `game.html` race state, `chooseRaceBowl()`, `startNpcRaceEscape()`, and `updateOriginalNpc()`.

**Interfaces:**
- Consumes: `RaceGraph`, `nearestRaceNode()`, and `findRacePath()` from Task 1.
- Produces: race target choice with a reachable bowl ID and waypoint path; bounded dead-end recovery state.

- [x] **Step 1: Add per-map race graph lifecycle state and per-NPC route state:** current path node IDs, waypoint cursor, progress sample, retry timer, and temporarily blocked edges with an expiry time. Reset all race route state in `startRun()` and when a map is replaced.
- [x] **Step 2: Replace line-of-sight bowl sorting in `chooseRaceBowl()` with path costs from NPC node to each remaining bowl's nearest reachable node.** Score nearby bowl clusters and corridor width/connectivity as small tie-breakers; skip all bowls without a path.
- [x] **Step 3: Change race steering to follow the next A* waypoint while retaining `moveOriginalNpc()` collision and floor checks.** Advance waypoint only when NPC reaches its capture radius; retain sprint stamina rules.
- [x] **Step 4: Detect lack of progress toward the current waypoint over a bounded interval.** Temporarily block the failed edge, re-run A* to the current target, and if that path fails, backtrack on the prior route to the nearest node with an unvisited branch before choosing a new reachable bowl.
- [x] **Step 5: Cap retries and handle no reachable bowl by stopping safely; retry after a short cooldown and when temporary blocked edges expire. Do not rotate through arbitrary headings.** Keep pickup checks idempotent so player/NPC cannot collect one bowl twice.
- [x] **Step 6: Inspect behavior paths in code for border dead ends, wall-blocked target, disconnected floor, all bowls collected, and brief collision delays; run inline script syntax parsing and `git diff --check`.**

### Task 3: Remove the race Gemini proxy

**Files:**
- Delete: `tools/race-ai-proxy.mjs`.

**Produces:** No race proxy or external AI dependency; chat AI remains separate.

- [x] Remove the unused race proxy and all race request/fallback code.
- [x] Remove race proxy setup and Gemini race configuration from README.

### Task 4: Make Hard local and balance player speed

**Files:**
- Modify: `game.html` map selection markup/styles, map selection handlers, race start/target-selection state, and status UI.

**Interfaces:**
- Consumes: Task 2 local target chooser/pathfinding.
- Produces: `raceDifficulty` (`normal` or `hard`), bounded two-bowl lookahead, and Hard-only NPC response tuning.

- [x] **Step 1: Add a difficulty selection panel that appears after the After the Rain card is selected, with Normal selected by default and an explicit start button.** Preserve direct selection behavior for other maps.
- [x] **Step 2: Store difficulty for the current race session and reset it predictably on a new selection/run.** Show the active local mode in the race status.
- [x] **Step 3: In Hard mode, rank a bounded shortlist using the route to the current bowl plus a weighted route to the next reachable bowl.** Keep all movement and replanning local.
- [x] **Step 4: Keep player walking/sprint speed standard in both modes. In active Hard races, make Original turn and accelerate faster, anticipate sprinting sooner, and replan sooner when stuck.**
- [x] **Step 5: Inspect target pickup, replanning, speed switching, and difficulty changes; use inline script syntax parsing and `git diff --check`.**

### Task 5: Document local strategic difficulty

**Files:**
- Modify: `README.md`.

**Interfaces:**
- Documents: Normal and Hard rules, NPC response differences, and local game startup.

- [x] **Step 1: Document that both modes work without network access, describe Hard's two-bowl lookahead and faster NPC reactions, and state that player speed remains standard.**
- [x] **Step 2: Remove obsolete race proxy setup and Gemini configuration instructions.**
- [x] **Step 3: Check README instructions and `git diff --check`.**

\n