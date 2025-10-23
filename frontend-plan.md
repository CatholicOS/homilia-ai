# Frontend Implementation Guide — ParishChat (Single Domain, Single-Tenant MVP)

This document describes the **high-level frontend implementation** for the ParishChat MVP using **React** (Vite), TailwindCSS, and a small set of libraries. It focuses on look & feel and basic functionality: a landing page with a parish selector, a chat page that uses backend-provided markdown for links, and a single admin dashboard (tabs: Upload, Documents, Other operations). No parishioner accounts for MVP. Links in chat answers open in a new tab; document access uses a base64-encoded S3 key in the URL (backend resolves to a presigned URL).

---

## Tech Stack
- **React + Vite** - Modern React development with fast build times
- **TypeScript** (recommended) - Type safety and better developer experience
- **TailwindCSS** - Utility-first CSS framework for styling
- **React Router** - Client-side routing
- **React Query (TanStack)** - Server state management & caching
- **axios** - HTTP client for API calls
- **react-markdown** - Render backend-provided markdown safely
- **PDF viewing**: `pdfjs-dist` or simple link to S3 presigned URL (open in new tab)
- **Optional**: Headless UI or simple component library for dialogs/tabs

---

## High-Level Pages & Routes

```
/                    -> Landing page (Parish selector + Quick start)
/chat               -> Chat page for selected parish (query param or internal state)
/admin              -> Admin dashboard (tabs: Upload | Documents | Ops)
/admin?tab=upload   -> Admin dashboard with Upload tab active
/admin?tab=documents-> Admin dashboard with Documents tab active
/admin?tab=ops      -> Admin dashboard with Ops tab active
/doc/:encoded_key   -> Doc viewer page (decodes base64 key, fetches presigned URL, and displays)
```

**Notes:**
- Single global domain (e.g., `parishchat.example.com`). Parish selection handled in-app (landing page).
- Multi-tenant support (per-parish slug/subdomain) can be added later.

---

## Primary Components (High-Level)

### Layout Components
- **`AppShell`** — Header (logo, parish selector dropdown persistent), main content container, footer.
- **`ParishSelector`** — Search + select parish; persists selection in localStorage.

### Pages
- **`LandingPage`** — Hero, parish selector, quick examples, "Start Chat" CTA.
- **`ChatPage`** — Chat UI (history, input, send), displays assistant answers and sources (rendered markdown).
- **`AdminDashboard`** — Single page with tab UI: Upload, Documents, Ops.
  - **`UploadTab`** — File input, title, type selector, submit button.
  - **`DocumentsTab`** — Table/list of uploaded docs with pagination, delete, reindex buttons.
  - **`OpsTab`** — Manual reindexing, ingest logs (basic).
- **`DocViewerPage`** — Decodes encoded S3 key, requests presigned URL from backend, either opens PDF inline or redirects to presigned URL.

### Small UI Components
- **`ChatBubble`** — User/assistant message (assistant includes sources area).
- **`MarkdownRenderer`** — Wraps `react-markdown` + sanitization.
- **`FileUploader`** — Wraps file select + validation.
- **`DocListItem`** — Row for a doc in admin list (download, delete, reindex).
- **`Toast` / `Alert`** — User messages for success / error.

---

## Data Flow & State

### React Query Usage
- `useQuery("/api/parishes")` — List parishes for selector.
- `useMutation("/api/upload")` — Upload files.
- `useQuery("/api/docs?parishId=...")` — Admin doc list.
- `useMutation("/api/chat")` — Send question, returns `{ answer: string, sources: string[] }`.
- `useQuery("/api/doc/presign?key=...")` — Get presigned URL for doc viewing.

### Minimal Local State
- **Selected parish**: Persisted to `localStorage` (`selectedParishId`).
- **Chat session**: In-memory list of messages (optionally persisted to localStorage for refresh).

---

## API Contracts (Frontend-Facing)

(Right now only chat and upload docs endpoints exist)

### `GET /api/parishes`
**Response:**
```json
[
  { "id": "1", "name": "St. John's Parish", "slug": "st-johns" },
  ...
]
```

### `POST /api/upload`
**FormData:** `{ file: File, title: string, source: string, parish_id?: string }`
**Response:**
```json
{ "file_id": "uuid", "status": "processing" }
```

### `GET /api/docs?parish_id=...`
**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Homily 2025-10-12",
    "filename": "homily.pdf",
    "s3_key": "uploads/...",
    "status": "processed"
  },
  ...
]
```

### `DELETE /api/docs/{id}`
**Response:**
```json
{ "status": "ok" }
```

### `POST /api/reindex/{doc_id}`
**Response:**
```json
{ "status": "started" }
```

### `POST /api/chat`
**Body:**
```json
{
  "message": "string"
}
```
**Response:**
```json
{
  "response": "string",
  "conversation_id": "string",
  "document_context": {},
  "sources": {}
}
```

### `GET /api/doc/presign?key={encoded_key}`
**Response:**
```json
{ "presigned_url": "https://s3...signature..." }
```

---

## Chat Page Specifics

### Layout
- **Left column** (or top on mobile): Chat messages list
- **Bottom**: Message input field, Send button
- **Header?** (optional): Short parish info / quick links

### UX Behavior
1. User enters question and hits Send.
2. Frontend POST `/api/chat` with `question`.
3. While waiting, show a loading indicator (skeleton or spinner).
4. On response:
   - Append assistant message to chat history.
   - Render response using react-markdown.
   - Ensure links in markdown open in new tab (`target="_blank" rel="noopener noreferrer"`).

### Rendering Markdown Safely
- Use `react-markdown` and a sanitizer plugin or renderers to avoid XSS.
- For links: Override renderer to add `target="_blank"` and `rel="noopener noreferrer"`.

---

## Doc Viewer Page (`/doc/:encoded_key`)

### Design
The URL contains a base64 (or similar) encoded S3 key: `https://parishchat.example.com/doc/{encoded_key}`

### On Mount
1. Redirect user to new page
2. Call `GET /documents/content/{endoded_file_id}` which returns 
```json
{
  "success": true,
  "content": "string",
  "content_type": "string",
  "filename": "string",
  "file_type": "string",
  "encoding": "base64 (optional)"
}
```
3. Display text

### Recommendation
- **MVP**: Redirect/open in new tab to the presigned URL (simple + reliable).
- If inline viewing is desired, use PDF.js with the presigned URL as the source.

---

## Admin Dashboard Details

Single page with 3 tabs (Upload, Documents, Ops). Implementation can be via query param (`?tab=upload`) or internal state.

### Upload Tab
**Fields:** Title, Source Type (homily, bulletin, announcement), file input

**On Submit:**
- POST to `/api/upload` with FormData
- Show toast: "Upload started — indexing will complete shortly."
- Optionally show returned `file_id` and allow navigating to Documents tab.

**Validation:**
- Accept only PDF/DOCX/TXT (configurable)
- Max file size limit (show error if exceeded)

### Documents Tab
**Table columns:** Title, Filename, Uploaded At, Status, Actions

**Actions:**
- **Download** — Use `/api/doc/presign` to get presigned URL and open in new tab
- **Delete** — `DELETE /api/docs/{id}` (confirm modal)
- **Reindex** — `POST /api/reindex/{doc_id}` (show notification)

**Features:** Pagination and simple search/filter by title or source type

### Ops Tab
- Manual reindex of all documents (dangerous — require confirmation)
- Simple ingest logs (if backend exposes)
- Export doc list as CSV (optional)

---

## Navigation & UX

### Top Navigation Bar
- **Logo** (left) — clicking returns to landing page
- **Parish selector** (center or right)
- **"Chat"** link
- **"Admin"** link (admin access only — for MVP you can show link always)

### Mobile
- Collapse into hamburger menu
- Chat should prioritize full-screen message area

### Accessibility
- Use semantic HTML (buttons, labels, forms)
- Provide `aria-label` for inputs and controls
- Keyboard navigation for chat input and file upload
- Color contrast and visible focus states

---

## Error Handling & Edge Cases

- **Network errors**: Show toasts with retry actions.
- **Upload failures**: Show detailed message from backend.
- **Long-running ingestion**: The backend replies with processing; admin can reindex or poll `/api/docs` to update status.
- **No documents indexed**: Chat should present a helpful fallback: "No documents available for this parish — try uploading one in the Admin."
- **Rate limiting**: Show helpful error message if backend returns 429.

---

## Testing & QA

- **Unit tests**: Component rendering, markdown renderer, link behavior.
- **Integration tests**: Mock API responses (MSW) to assert chat flow, upload flow, and doc viewing behavior.
- **Manual E2E**: Upload a sample PDF in Admin, then ask a relevant question on Chat and confirm returned sources open the doc viewer.

---

## Developer Ergonomics & Recommended Libraries

- `react-router-dom` — routing
- `@tanstack/react-query` — data fetching + cache
- `axios` — HTTP client
- `react-markdown` + `rehype-sanitize` — markdown rendering + sanitization
- `clsx` — conditional class names
- `pdfjs-dist` (optional) — for inline viewing
- `zustand` or simple React Context — for global state (selected parish)

---

## Example Minimal Component Usage (Pseudocode)

```tsx
// ChatPage.tsx (simplified)
const ChatPage = () => {
  const selectedParish = useSelectedParish();
  const [messages, setMessages] = useState<Message[]>([]);
  const mutation = useMutation((q) => 
    axios.post('/api/chat', { parish_id: selectedParish.id, question: q })
  );

  const send = async (question) => {
    setMessages([...messages, { role: 'user', text: question }]);
    const res = await mutation.mutateAsync(question);
    setMessages([
      ...messages, 
      { role: 'user', text: question }, 
      { role: 'assistant', text: res.data.answer, sourcesMarkdown: res.data.sources_markdown }
    ]);
  };

  return (
    <div>
      <MessageList messages={messages} />
      <ChatInput onSend={send}/>
    </div>
  );
};
```

> In `MessageList`, use `react-markdown` for `sources_markdown` and override the link renderer to open in a new tab.

---

## Deployment Notes

- Frontend build served via Vercel, Netlify, or S3+CloudFront.
- Environment variables for production: `VITE_API_URL`.
- Ensure CORS configured on backend to allow the frontend origin.
- For demo/staging: set `VITE_API_URL` to staging backend.

---

## Future Enhancements (Frontend)

- Add login for admin with JWT and protected admin route.
- Add streaming chat (SSE or WebSocket) for incremental LLM responses.
- Add inline document text viewer (parsed text with highlights on click to show source snippet).
- Add ability to pin admin-provided Q/A to the chat as authoritative responses.

---

## Summary

This high-level guide provides the UI pages, components, data flow, and API contracts needed to implement the landing page, chat page, and admin dashboard for the ParishChat MVP. The frontend treats backend-provided link markdown as authoritative (rendered with safety), opens docs in new tabs, and resolves doc access via base64-encoded keys and backend presigned URLs.
