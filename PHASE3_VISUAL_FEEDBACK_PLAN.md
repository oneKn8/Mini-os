# Phase 3: Live Visual Feedback System

## Goal
Build Cursor-style real-time visual feedback that shows what the agent is doing, what it's working on, and what it has completed. Users should see live highlighting and previews as the agent works.

## Problem
Currently the agent works invisibly. Users don't see:
- Which UI elements the agent is interacting with
- Real-time progress on multi-step operations
- Preview of changes before they're applied
- Visual confirmation of completed actions

## Solution: 3-Layer Visual Feedback

### 1. Real-Time Action Highlighting
**What:** Highlight UI elements as agent works on them
**How:**
- WebSocket streaming of agent actions
- CSS selector-based element targeting
- Visual states: thinking → working → done
- Frontend overlay system with highlights

**Example:**
```
Agent: "Checking your emails..."
→ Inbox sidebar glows blue (thinking)
→ Email list highlights yellow (working)
→ Checkmark animation (done)
```

### 2. Ghost Previews
**What:** Show preview of changes before applying
**How:**
- Render "ghost" components in preview mode
- Semi-transparent overlay of what will be created
- Accept/reject UI for user confirmation

**Example:**
```
Agent: "Creating calendar event..."
→ Ghost event appears on calendar (50% opacity)
→ User sees preview before it's created
→ Click to confirm or modify
```

### 3. Progress Visualization
**What:** Visual progress bar for multi-step operations
**How:**
- Step-by-step progress indicator
- Current action display
- Estimated completion time
- Tool execution timeline

**Example:**
```
Query: "What's my day like?"
[===75%===    ] 3/4 tools complete
✓ Calendar checked
✓ Weather retrieved
✓ Emails scanned
⟳ Synthesizing response...
```

## Implementation Plan

### Backend (orchestrator/)
1. **streaming.py** - Add visual feedback events
   - `emit_highlight(selector, state, message)`
   - `emit_ghost_preview(component_type, data)`
   - `emit_progress(step, total, action)`

2. **enhanced_agent.py** - Integrate visual streaming
   - Emit highlights during tool execution
   - Send ghost previews for create operations
   - Stream progress for multi-tool queries

### Frontend (frontend/src/)
1. **components/VisualFeedback/**
   - `ElementHighlight.tsx` - CSS selector highlighting
   - `GhostPreview.tsx` - Preview overlays
   - `ProgressTimeline.tsx` - Multi-step progress

2. **hooks/useAgentFeedback.ts**
   - Listen to WebSocket visual events
   - Manage highlight state
   - Handle preview confirmations

3. **Integration with existing UI**
   - Inbox: Highlight emails being processed
   - Calendar: Ghost events for creates
   - Chat: Progress timeline for queries

## Success Metrics
- ✓ User sees which element agent is working on
- ✓ Preview shown before creating/modifying items
- ✓ Real-time progress for 3+ tool queries
- ✓ Visual confirmation when actions complete
- ✓ <100ms latency for highlight updates

## Technical Requirements
- WebSocket support (already exists)
- CSS selector targeting
- React overlay system
- Z-index management for highlights
- Animation performance (60fps)

## Deliverables
1. Backend visual event system
2. Frontend highlight components
3. Ghost preview system
4. Progress timeline
5. Integration with inbox, calendar, chat
6. Tests for visual feedback accuracy

## Estimated Complexity
- Backend: ~400 lines (streaming events)
- Frontend: ~800 lines (3 components + hooks)
- Integration: ~200 lines
- Tests: ~300 lines
- Total: ~1700 lines

## Next Steps After Phase 3
- Phase 4: Proactive Suggestions (predict user needs)
- Phase 5: Advanced Analytics (insight dashboard)
