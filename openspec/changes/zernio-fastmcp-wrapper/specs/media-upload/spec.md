## ADDED Requirements

### Requirement: Upload media via URL with presigned flow
The `media_upload` tool SHALL accept a publicly accessible URL, fetch the bytes server-side, upload via Zernio's presigned GCS flow (`POST /v1/media/presign` → `PUT` to GCS), and return the `publicUrl` for use in `posts_create`.

Supported formats: JPG, PNG, WebP, GIF, MP4, MOV, WebM.

#### Scenario: Upload image from URL
- **WHEN** `media_upload` is called with `url="https://example.com/photo.jpg"`
- **THEN** server fetches bytes, calls presign, uploads to GCS, returns `{ publicUrl: "https://storage.zernio.com/..." }`

#### Scenario: URL returns non-media content type
- **WHEN** `media_upload` is called with a URL that returns `text/html`
- **THEN** the tool returns an error: "URL does not point to a supported media file"

### Requirement: Fallback base64 path for mobile attachments
The `media_upload` tool SHALL also accept a `base64_data` parameter with a `mime_type` for images under 2MB. This covers the Claude mobile use case where users attach camera roll images that arrive as base64 in the conversation. The docstring MUST state: "For images under 2MB, pass base64_data and mime_type. For larger files or videos, provide a publicly accessible URL."

#### Scenario: Mobile camera roll image
- **WHEN** `media_upload` is called with `base64_data="iVBOR..."` and `mime_type="image/png"` (800KB image)
- **THEN** server decodes base64, uploads via presign flow, returns `publicUrl`

#### Scenario: Base64 exceeds 2MB limit
- **WHEN** `media_upload` is called with base64_data that decodes to 3MB
- **THEN** the tool returns an error: "Image exceeds 2MB base64 limit. Please provide a URL instead."

#### Scenario: Neither URL nor base64 provided
- **WHEN** `media_upload` is called without `url` or `base64_data`
- **THEN** the tool returns an error explaining both input options

### Requirement: SSRF protection on URL fetching
The server MUST validate URLs before fetching:
- Reject private/internal IPs (10.x, 172.16-31.x, 192.168.x, 127.x, ::1, link-local)
- Reject non-HTTP(S) schemes (no file://, ftp://, etc.)
- Enforce 100MB max response size
- Set httpx timeout to 30 seconds
- Limit redirects to same-origin only (or disable redirect following)

#### Scenario: SSRF attempt with internal IP
- **WHEN** `media_upload` is called with `url="http://192.168.1.1/admin"`
- **THEN** the tool rejects the URL before any network request is made

#### Scenario: SSRF attempt with non-HTTP scheme
- **WHEN** `media_upload` is called with `url="file:///etc/passwd"`
- **THEN** the tool rejects the URL

#### Scenario: Response exceeds size limit
- **WHEN** the URL response exceeds 100MB
- **THEN** the download is aborted and an error is returned

### Requirement: ToolAnnotations for media_upload
- **WHEN** `media_upload` is registered
- **THEN** it MUST have `ToolAnnotations(readOnlyHint=False, idempotentHint=False)`

#### Scenario: Tool registration
- **WHEN** the FastMCP server starts
- **THEN** `media_upload` is registered with destructive write annotations
