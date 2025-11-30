# Inbox & Agent Overhaul Plan

This document lays out a concrete plan to turn the current inbox + agent experience into something that feels much closer to Gmail + Cursor/Claude, both in terms of **email fidelity** and **agent UX**.

The focus areas:

1. Email fidelity – full HTML bodies, calendar invites, better rendering.
2. Inbox completeness & structure – more than 50 emails, real tabs/folders.
3. Agent experience – live previews in the main pane, visible reasoning, fast feedback.
4. Architecture & performance – how the pieces should fit so it stays maintainable.

---

## 0. Current Situation (What’s Wrong)

### Email ingestion & rendering

- Gmail sync only fetches a limited slice of messages (single page, `maxResults=50`).
- `_extract_body` previously preferred `text/plain`, so many stored `items.body_full` values are **plain text**, not HTML.
- Existing rows in `items` keep that degraded body; refresh only inserts new messages, it never upgrades old ones.
- `EmailViewer` has:
  - A plain‑text cleaner (`cleanEmailBody`) that is better than raw HTML, but still destroys layout.
  - An HTML rendering path, but many messages simply don’t have good HTML in `body_full`.
- Calendar invites (like Google Calendar cancellation emails) rely on `text/calendar` and structured metadata. We only show an unstructured text block, while Gmail renders a rich status card.

### Inbox data & structure

- `sync_gmail` calls `GmailClient.fetch_messages(max_results=50)` **once**, no pagination or date window.
- `/api/inbox` returns at most 200 items per request with no cursor/pagination; that “200” only ever comes from whatever small set is in the DB.
- Inbox tabs/folders (Primary / Promotions / Sent / Spam / Trash / All) operate on that limited dataset, so “Primary” might show only a handful of messages even though Gmail shows thousands.

### Agent UX

- Back‑end already emits rich events (`reasoning`, `thought`, `screen_control`, `preview`, `approval_required`), and the front‑end has:
  - `screenController` for agent cursor, thought bubbles, and generic previews.
  - `chatStore` for streaming events and reasoning.
  - `EmailComposer`, `InboxView`, `EmailViewer` as core UI pieces.
- But the integration is partial:
  - Previews exist but **don’t fully drive the main center pane** (email draft as live preview).
  - Agent reasoning is present in state but not surfaced in a polished way.
  - The UX feels like a slow “chat bot” rather than a live, visual, Cursor‑style assistant.

---

## 1. Email Fidelity – Match Gmail’s Rendering

Goal: for normal HTML emails and calendar invites, the content in our viewer should be recognizably close to Gmail’s rendering, while staying safe and consistent with the dark theme.

### 1.1 Improve Gmail ingestion (`GmailClient._extract_body`)

**Files:**
- `backend/integrations/gmail.py`

**Problems today:**
- Only looks at limited levels of `payload.parts`.
- Picks the first `text/plain` it finds, so rich HTML or invite layouts are lost.

**Plan:**

1. Implement a **recursive multipart walker**:
   - Traverse the full `payload` tree.
   - For each part, consider:
     - `mimeType` (e.g., `text/html`, `text/plain`, `multipart/alternative`, `text/calendar`).
     - `body.data` (base64 content).
   - Keep:
     - `html_parts: List[str]`
     - `text_parts: List[str]`
     - `calendar_parts: List[str]` (`text/calendar`)

2. Selection strategy:
   - Prefer the innermost `multipart/alternative`’s `text/html` (best candidate).
   - If none, use any `text/html`.
   - Else fall back to the “best” `text/plain` candidate.

3. Calendar metadata:
   - Capture the **first** `text/calendar` body into `raw_metadata.gmail.calendar_body`.
   - Optionally also store `raw_metadata.gmail.calendar_content_type` / `charset` for debugging.

4. Keep enough raw data for debugging:
   - Optionally store key pieces of the raw Gmail payload:
     - `raw_metadata.gmail.payload_headers` (sanitized subset of headers).
     - Avoid storing the full payload if size is a concern; store only what’s useful for debugging rendering issues.

### 1.2 Backfill existing `Item` rows with HTML

**Files:**
- `backend/ingestion/sync_service.py`
- A new CLI/management script (e.g., `scripts/resync_gmail_items.py`) or admin endpoint.

**Why:**  
Even after fixing `_extract_body`, existing DB records still contain the old plain‑text bodies. Without a backfill, your promo/ invite emails will continue to look wrong.

**Plan:**

1. Add a **“resync Gmail messages”** helper in `SyncService`:
   - Input: `user_id` and optional `limit`/`date_range`.
   - For each Gmail `Item` belonging to that user:
     1. Use `GmailClient` with the account’s tokens.
     2. Call `users.messages.get(userId="me", id=item.source_id, format="full")`.
     3. Run `_normalize_message` on that full message.
     4. Update the existing `Item` fields:
        - `body_full`, `body_preview`
        - `raw_metadata.gmail.labels`
        - `raw_metadata.gmail.calendar_body` (if present)
   - Do this in batches (e.g., 50–100 at a time) to avoid long transactions.

2. Provide a CLI or admin endpoint:
   - CLI example:
     - `python -m backend.scripts.resync_gmail --user USER_ID --limit 200 --newer_than 365d`
   - Endpoint example:
     - `POST /api/admin/resync-gmail` with body `{ "user_id": "...", "limit": 200, "newer_than_days": 365 }`

3. Workflow:
   - Start with a small sample (e.g., 20 promo + 20 calendar emails).
   - Verify visual output in the inbox.
   - Gradually widen the range (e.g., last 6–12 months).

### 1.3 HTML rendering & safety in `EmailViewer`

**Files:**
- `frontend/src/components/Inbox/EmailViewer.tsx`

**Goals:**
- Render HTML nearly as Gmail does, but safely.
- Keep the option to switch to plain‑text view.

**Plan:**

1. **Sanitizer adjustments:**
   - Keep the DOM‑based sanitizer, but:
     - Allow a controlled subset of inline styles:
       - `color`, `background`/`background-color`, `font-size`, `font-weight`, `text-align`, `margin`, `padding`, `border`, `border-radius`, `line-height`.
     - Preserve `table`, `tr`, `td`, `th`, `colgroup`, and width/align attributes (many emails use table layout).
     - Drop clearly dangerous patterns:
       - `expression(`, `javascript:`, `data:text/html`, any `on*` handlers.

2. **Visual container:**
   - Wrap the email HTML in a “paper” card:
     - `max-w-[720px] mx-auto bg-white text-black rounded-xl shadow px-8 py-6` for HTML view.
     - Dark theme stays around it; the email content itself can be light like Gmail.
   - Keep plain view as you have (`whitespace-pre-line`, dark text).

3. **HTML / Plain toggle UX:**
   - Default to HTML if `hasHtml` is true and sanitized HTML is non‑empty.
   - Always show the toggle; disable HTML when there is no HTML in the body.

### 1.4 Calendar invites & event updates

**Goal:**  
Calendar invites/cancellations should show a structured card (status, Zoom link, when, guests), not just raw text.

**Plan:**

1. Add a small ICS parser on the backend or frontend:
   - Backend:
     - Parse `raw_metadata.gmail.calendar_body` into structured data and store under `raw_metadata.calendar_parsed` (summary, start, end, location, attendees, status).
   - Or frontend:
     - Quick JS parser that extracts key lines (`SUMMARY:`, `DTSTART:`, `DTEND:`, `LOCATION:`, `STATUS:`, `ATTENDEE:`).

2. New `CalendarInviteCard` component:
   - Displays:
     - Status banner (e.g., red for canceled).
     - Title + meeting link.
     - When, timezone, recurrence if any.
     - Guest list (name/email, maybe icons).

3. In `EmailViewer`:
   - If `item.raw_metadata.calendar_parsed` (or ICS body) is present:
     - Render `CalendarInviteCard` above the message body.

---

## 2. Inbox Completeness & Structure

Goal: show a realistic subset of your Gmail (hundreds+ messages), with tabs/folders similar to Gmail’s Primary/Promotions/Social/Updates + Sent/Spam/Trash/All, and add pagination so the list can grow.

### 2.1 Expand Gmail sync

**Files:**
- `backend/integrations/gmail.py`
- `backend/ingestion/sync_service.py`

**Plan:**

1. Extend `GmailClient.fetch_messages`:
   - Support `page_token` and return `(messages, next_page_token)`.
   - Accept Gmail query string (`q`) for date range: e.g., `"newer_than:365d"`.

2. Update `sync_gmail`:
   - Loop:
     - Call `fetch_messages(max_results=100, page_token=...)`.
     - Insert new `Item`s (same as today) if they don’t exist.
     - Stop when:
       - Reached `TARGET_COUNT` (e.g., 500–1000 emails), or
       - No `nextPageToken`.
   - Use `q="newer_than:365d"` or similar to limit to the past year initially.

3. Track sync progress per account:
   - Optionally store `raw_metadata.gmail.last_page_token` or a last synced `internalDate` in `ConnectedAccount.raw_metadata` to support incremental extension later.

### 2.2 Backend pagination for `/api/inbox`

**Files:**
- `backend/api/routes/inbox.py`

**Plan:**

1. Add query params:
   - `cursor: Optional[str]` – ISO timestamp or encoded cursor.
   - `page_size: int = 50` – capped at e.g. 100.

2. Use keyset pagination:
   - Base query filters by `Item.is_archived == False` (or folder logic).
   - If `cursor` provided:
     - Add `Item.received_datetime < cursor_datetime`.
   - Order by `received_datetime DESC`, `LIMIT page_size`.

3. Response structure:
   ```jsonc
   {
     "items": [...],
     "next_cursor": "2025-11-28T00:12:34.000Z" | null
   }
   ```

4. Keep the current Gmail category/folder annotations:
   - `gmail_category`, `folder`, `gmail_labels`.

### 2.3 Frontend “Load more” + tabs/folders

**Files:**
- `frontend/src/api/inbox.ts`
- `frontend/src/hooks/useInbox.ts`
- `frontend/src/pages/InboxView.tsx`
- `frontend/src/components/Inbox/EmailItem.tsx`

**Plan:**

1. Update `fetchInboxItems` / `useInbox`:
   - Accept `{ filter, cursor, pageSize }`.
   - Return `{ items, next_cursor }`.

2. In `InboxView`:
   - Keep local state:
     - `pages: InboxItem[][]`
     - `cursor: string | null`
     - `isLoadingMore: boolean`
   - On initial load:
     - Fetch first page (no cursor).
   - “Load more” button at bottom:
     - If `next_cursor` is non‑null, fetch next page and append to `pages`.
   - `filteredItems` = flat map of `pages` (plus search filter).

3. Tabs vs folders:
   - Tabs for Gmail categories (Primary / Promotions / Social / Updates) → send `filter=primary` etc.
   - Folder buttons for Sent / Spam / Trash / All → send `filter=sent`, `filter=spam`, etc.

4. Row chips (already added):
   - Keep `folder` and `gmail_category` chips on `EmailItem` so you always know where a message belongs (Inbox/Promotions/Sent/Spam/...).

---

## 3. Agent UX for Inbox & Drafting

Goal: when you ask the agent to “draft a reply” or “compose an email”, you see:

- Instant visual action:
  - Agent cursor moves.
  - Center pane shows a live email draft (even if empty) within a second or two.
- Streaming updates:
  - Draft text updates as the LLM writes.
  - Reasoning appears in the chat sidebar and, optionally, as thought bubbles.
- Clear approvals:
  - You edit the draft in the center.
  - Approve or reject; agent executes or discards and celebrates/summarizes.

### 3.1 Define a stable preview contract

**Events from backend → frontend:**

```jsonc
{
  "type": "preview",
  "page": "/inbox",
  "preview_type": "email_draft",
  "cursor": "[data-email-list]",  // optional CSS selector
  "data": {
    "id": "draft-123",            // stable ID for this preview
    "mode": "reply",              // 'reply' | 'new' | 'forward'
    "to": "someone@example.com",
    "subject": "Re: ...",
    "body": "Streaming body text...",
    "in_reply_to_item_id": "<Item.id>",
    "metadata": {
      "gmail_thread_id": "...",
      "original_message_id": "..."
    }
  }
}
```

Follow‑up `preview` events with the same `data.id` update the draft as it streams.

### 3.2 Wire previews into `InboxView`

**Files:**
- `frontend/src/store/screenController.ts` (already has `addPreview`, `getPreviewsForPage`)
- `frontend/src/pages/InboxView.tsx`
- `frontend/src/components/Inbox/EmailComposer.tsx`

**Plan:**

1. In `InboxView`, where you determine which composer to show:
   - Call `useScreenUpdates('/inbox')` and inspect `previews`.
   - If there is an `email_draft` preview with `status === 'pending'`:
     - Prefer that over `currentDraft`/`manualReplyDraft`/`newComposeDraft`.
     - Pass `preview.data` into `EmailComposer` as the initial draft.

2. Support live updates:
   - When `addPreview` is called with the same `id`, have it **replace** the stored preview (rather than adding a new one), so the composer sees the latest `body`.

3. Confirm / cancel:
   - When an email is sent (manual or agent‑approved):
     - Backend emits an event (e.g., `preview_confirmed` or `auto_approved` + `screen_control: release`).
     - `chatStore` calls `useScreenController.getState().confirmPreview(id)` or `cancelPreview(id)`.
   - `InboxView` then returns to the normal viewer/list layout.

### 3.3 Thought bubbles and reasoning visibility

**Files:**
- `frontend/src/store/screenController.ts`
- `frontend/src/store/chatStore.ts`
- `frontend/src/components/ThoughtBubble.tsx`

**Plan:**

1. Ensure backend emits:
   - `type: 'thought'` with:
     - `content`: short reasoning blurb.
     - `cursor`: CSS selector to anchor the bubble near relevant UI.
2. `chatStore` already handles `event.type === 'thought'` by calling:
   - `const sc = useScreenController.getState(); sc.showThought(event.content, event.cursor)`.
3. `ThoughtBubble` component:
   - Subscribe to `useScreenController` (`currentThought`, `thoughtVisible`, `thoughtPosition`).
   - Render a minimal bubble that auto‑hides after ~4 seconds (already implemented in `showThought`).

### 3.4 Latency & responsiveness improvements

This is more on the backend/orchestrator + prompt side, but it matters for UX:

1. **Early preview:**
   - As soon as the agent decides “I will draft an email”, it should:
     - Emit a `preview` event with a skeleton draft.
     - Emit `screen_control` (`take` + `focus: '/inbox'`) so the UI jumps to the inbox view.
2. **Streaming draft text:**
   - Instead of waiting for the LLM to complete the full email, stream partial content:
     - Each chunk updates `data.body` in a new `preview` event.
3. **Progress & status:**
   - Emit `progress` events (`current_step`, `total_steps`, `percent_complete`) that `chatStore` already knows how to display.
4. **Prompt tuning:**
   - Use specialized system prompts per tool:
     - Email drafting agent: “You are a fast email drafting agent… keep reasoning short, show draft early, refine in place.”
   - Avoid huge global plans when only a simple reply is needed.

---

## 4. Architecture & Next Steps

### Where React fits (and why it’s fine)

React is not the bottleneck. The slow feeling and partial UX come from:

- Limited, non‑paginated data.
- Missing HTML in stored emails.
- Agent events not fully wired to the UI.
- Overly sequential workflows on the backend.

React + TypeScript is appropriate for:

- Complex, real‑time UI (inbox, sidebars, streaming content).
- Agent cursor visuals, thought bubbles, overlays.
- Rapid iteration on components like `EmailViewer`/`EmailComposer`.

If performance ever becomes a true bottleneck, you can:

- Add Rust/Go microservices behind your existing API for heavy indexing/search.
- Keep the React UI and state stores as they are.

### Suggested implementation order

1. **Email fidelity (Stage 1)**
   - Implement robust `_extract_body`.
   - Add calendar body capture and (optionally) parsing.
   - Run a backfill on a small subset of Gmail items and visually verify HTML.
   - Upgrade `EmailViewer` HTML rendering (paper card, relaxed sanitizer).

2. **Inbox completeness & pagination (Stage 2)**
   - Expand Gmail sync with pagination and date windows.
   - Add cursor‑based pagination to `/api/inbox`.
   - Implement “Load more” in `InboxView`.

3. **Agent live previews for email (Stage 3)**
   - Stabilize the `preview` event contract for `email_draft`.
   - Wire `screenController` previews into `InboxView` → `EmailComposer`.
   - Ensure thoughts/reasoning are surfaced during drafting.

4. **Agent performance & polish (Stage 4)**
   - Refine prompts for speed and minimal delay to first preview.
   - Tune progress/insight events and visual indicators (cursor movement, thought bubbles, progress bar).
   - Add small UX enhancements (e.g., “Agent is drafting…” banners, nicer empty states).

This plan turns your current “rough work” into a clear path: fix the data, then the rendering, then the inbox scale, then the agent UX. Once Stage 1–3 are in place, the app should feel much closer to what you see in Gmail + Cursor/Claude for the inbox use case. 

