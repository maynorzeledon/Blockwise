# Blockwise

A bilingual Minecraft discovery app: short facts, original illustrated cards, full articles and Minecraft Wiki source links. Includes topic preferences, search, bookmarks, read history, sharing, English/Spanish read-aloud, light/dark mode, JSON export/import, optional recovery-code backups, and a moderated report/suggestion inbox.

## Status

Initial collection: eight articles in English and Spanish. Direct retrieval of the current Minecraft Wiki pages was blocked during development. Articles show whether indexed excerpts were reviewed or direct verification is still pending. Do not call this collection fully fact-checked. `web/facts.json` is the editable content source. Spanish content is an original translation; links go to the English Wiki.

No email/account needed. Local data stays on the device. Recovery codes are private bearer secrets: losing one loses access to its online backup. Save/restore is explicit (not automatic merging). Reports never publish automatically.

## Cloudflare Workers

Requires a Cloudflare account with R2 enabled. Provider quotas/pricing apply; no paid API or AI key is required by the app.

```sh
node scripts/bundle.mjs
npx wrangler login
npx wrangler r2 bucket create blockwise-data
npx wrangler deploy
```

`wrangler.jsonc` binds `BUCKET` to `blockwise-data`. The worker serves the app and `/api/submissions` and `/api/progress` from the same origin. For Git-connected Workers builds, use `node scripts/bundle.mjs` as the build command and `npx wrangler deploy` as deployment command. No frontend framework installation is required.

### Reviewing reports

Open Cloudflare → R2 → `blockwise-data` → `submissions/`. Each submission is a JSON object with type, proposed fact, Wiki URL, explanation, language, date, and pending status. Review the source and update `web/facts.json` manually; no submission is automatically trusted. Delete reviewed objects when appropriate. Old `limits/` objects can be removed with a one-day lifecycle rule. Device IPs are not stored in report objects; hourly throttle keys contain a hash of IP and hour. Platform access logs may be retained by the host.

Public deployment includes validation, body limits, an invisible spam field, and a best-effort R2 throttle. R2 read/write throttling is not atomic under concurrent requests. For a high-traffic public release, configure edge rate limits or Turnstile. No public report-reading endpoint is exposed.

## Android APK

A native Android WebView shell bundles all eight articles for offline use, saves local progress, exports/imports backups, opens Wiki links in the system browser, and uses the device TTS voice and share sheet. Android 8+ (API 26). No login or API keys are embedded.

GitHub Actions → **Build Android APK** runs on main pushes or manual dispatch. Download `Blockwise-Android-APK` from the completed run and extract `app-debug.apk`. This is a debug-signed testing APK, not a store release. Debug signing keys generated on separate runners can differ; an update may require reinstalling, so export a backup first. For stable public distribution, configure a persistent private release keystore and release signing; do not commit signing keys.

In the APK, open Settings → Website connection and enter your public Cloudflare origin to enable reports/backups without reinstalling. To bake in a default before building, set the repository variable `BLOCKWISE_API_ORIGIN` to the public Cloudflare origin (no trailing slash), or enter it in manual workflow dispatch. An APK built without it still supports offline reading and local progress; online requests fail visibly and keep form text. A private preview URL is not a substitute for the public API origin.

Local build (JDK 17, Gradle 8.9, Android SDK 35 installed):

```sh
BLOCKWISE_API_ORIGIN=https://your-worker.example.workers.dev node scripts/android-assets.mjs
gradle -p android assembleDebug
```

The API accepts the packaged app origin `https://blockwise.local` through narrow CORS. No browser credentials are sent by the APK. The Android assets load under that reserved local origin and external pages open outside the bridge-enabled WebView.

## Windows and web installation

This is an installable PWA. Use Edge/Chrome's install option on Windows or a compatible Android browser. This produces a desktop app window and offline reading after the first successful online visit. A Windows `.exe` installer is not included. Reports/backups still require connectivity. The Android APK bundles content and does not need that first website visit.

## Development and checks

```sh
node --check web/app.js
node tests/backend.mjs
node tests/frontend.mjs
node scripts/bundle.mjs
bash scripts/build.sh
node scripts/validate-artifact.mjs
```

Backend checks exercise validation, origin checks, spam trap, limits, submission persistence, independent recovery codes, restore, and deletion. Browser/device testing is still required: this environment did not provide the supported browser QA integration or an Android emulator.

## Content and artwork

Thumbnails now use downloaded Minecraft screenshots and official Minecraft.net game images, not generated illustrations. `web/media-catalog.json` retains image source URLs, credits, and missing-mob entries. The 65-image starter catalog covers 55 mob subjects plus topic images; it is not yet a complete image set for every mob. `web/media/` is bundled for offline use. Image rights remain with Mojang/Microsoft and credited sources; the MIT code license does not apply to these images. Text is original summary/explanation informed by Minecraft Wiki contributors. Wiki content is CC BY-NC-SA 3.0: https://minecraft.wiki/w/Minecraft_Wiki:Copyrights . Treat Wiki-derived text in this project under CC BY-NC-SA 3.0 and preserve attribution and source links. Check separate asset rights before adding Wiki images. Code is MIT licensed (see LICENSE). Minecraft is a Mojang/Microsoft trademark. This is an unofficial fan project, not approved by or affiliated with Mojang or Microsoft.

## v0.2 — tags, versions and contribution media

Facts have multiple `topics`, many `tags`, and per-edition `versionRanges` (`exact`, `range`, or `unknown`). Published version claims require a review flag; the initial eight articles have unknown/unverified ranges rather than fabricated support claims. Filtering an explicit version excludes unverified ranges by default; the visitor may opt to include them. Exact snapshot/pre-release labels are supported. Release ranges compare numeric parts (1.21.10 follows 1.21.9), not decimal numbers.

The topic list includes Survival, Creative, Hardcore, Technical Minecraft, Redstone, Commands, Mods, Building and more. Empty topics accept contributions; no facts are invented to fill them. The searchable tag vocabulary covers mobs and mechanics and accepts additional custom tags.

`POST /api/submissions` accepts multipart FormData with a JSON `payload` and up to four `media` files. The payload includes topics, tags, edition/version scopes, version notes, mod/loader details, a required Minecraft Wiki URL, and optional media credit/source. Files allow JPG/PNG/WebP/GIF up to 5 MiB each or MP4/WebM up to 25 MiB each; combined media must fit 30 MiB. Uploads require an explicit rights checkbox. MIME signatures and sizes are checked; this is not a malware scanning service. Invalid uploads preserve the form for retry.

Submitted media is stored privately under `submission-media/<submission-id>/`; the pending submission JSON records its object keys. Open these keys through the owner Cloudflare R2 dashboard when reviewing a fact. There is no public media retrieval endpoint. Version verification flags are always reset to false for submissions. Publishing a contribution still requires manual review and source validation.

The Android file chooser now accepts multiple images/videos as well as backup JSON files. APK version is 0.2.0. A newly generated debug key may require uninstalling an earlier test APK; export progress first.

`worker/index.js` is generated and ignored. Always run `node scripts/bundle.mjs` before direct Wrangler deployment (the Sites build script does this automatically).

## v0.3 — shared encyclopedia and discovery feed

The feed and reference library are now separate. `facts.json` contains discovery cards with a `targetId`; multiple cards route to one canonical `entries.json` mob page, with the selected discovery highlighted and its source context available. Resource pages such as Gunpowder have neutral descriptions and images rather than borrowing a random fun fact. Underlined terms open a general hover/focus preview; a separate ⓘ button supports touch access. Clicking opens the full local page. The library includes descriptions, source statistics, behavior, spawning, drops, interactions/trading where present, selected historical milestones, related pages, and original source links.

Coverage is recorded in `web/coverage.json`: 898 cards, 248 reference entries, and 93 mob/special-variant pages. 82 mob entries have ten or more cards. Eleven deliberately have fewer: cod, endermite, snow golem, tadpole, tropical fish, vex, parched, giant, killer bunny, NPC and agent. The latter entries include unused Java variants and Education-specific creatures; they are not all naturally spawning mobs in both editions. Source-contained statements and edition qualifiers take priority over meeting a quota.

Most source text and tables are adapted from the Minecraft Wiki English archive dated **2025-11-05**, accessed through its public Kiwix mirror. This is explicitly marked on pages and is not verification of current game behavior. The sulfur cube postdates that archive and uses separate Java 26.2 release-note claims dated **2026-06-16**, alongside its Minecraft Wiki link. Spanish reference translations are labeled as machine drafts; consult the original English source for exact wording. Do not advertise the full collection as currently verified or native-reviewed Spanish.

`web/reference-images/` contains sourced game renders, displayed on a bright neutral surface in both themes. The old dark bed thumbnail now uses a bright bed game render. Images remain subject to their original rights and attribution. No thumbnails were generated by AI.

Content preparation scripts are `scripts/import-wiki.py`, `scripts/build-reference-data.py` and `scripts/finalize-reference.py`. They are editorial build helpers, not runtime services; they require their documented local source files, parsing/image dependencies and local translation model. Model weights, raw Wiki downloads and translation caches are not shipped with the app. Published JSON is committed so neither the website nor APK needs an AI API.

Static text assets are precompressed in the generated Worker bundle. Binary image assets stay in their native encoding. Source scripts and Android assets remain ordinary local files. The build checks support Cloudflare's compressed Worker size limit.

The larger library raises progress-backup limits to 5,000 identifiers and increases JSON backup import/export capacity. No email or user account is introduced.

### v0.4 fact database, edition picker and discovery

Open `/#database` for the current published fact collection. The table is built from
`web/facts.json`, so future published facts appear automatically. Search covers both
languages, tags and IDs; edition/version filters and CSV/JSON exports operate on
all matching rows, even when only 50 rows are displayed. Exports contain both
language descriptions, source context, tags, topics, edition scopes, verification
flags, source dates, Blockwise links and original Wiki links. CSV text is quoted
and spreadsheet formula prefixes are escaped. The APK can save catalogue exports
in Downloads (Android 10+); older devices use the share sheet.

`web/versions.json` is a sourced suggestion index for Java, Bedrock, Pocket,
individual Legacy Console platforms, 3DS, Education, Pi, MinecraftEdu and other
historical editions. The historical Wiki archive is dated 2025-11-05; the Java
launcher manifest supplements it. This index is incomplete, especially for old
platform derivatives and post-archive Bedrock builds. Every edition accepts a
custom exact build name rather than pretending missing releases do not exist.
A version appearing in the picker does not establish that a fact applies to it.
Unknown/unverified ranges are excluded by default when a version filter is set.
Non-numeric development ranges can be submitted for review, but are not silently
compared as semantic release versions. Java + Bedrock submissions expand into two
separate scopes; platform-specific facts must keep their scopes separate.

Refresh the source index with `python3 scripts/update-version-catalog.py`
(Python standard library and curl). All records retain Wiki attribution links.

Discovery ordering uses a per-session random seed, unread/recent-exposure
preferences and round-robin entity grouping to avoid long runs of the same mob.
The local exposure list contains only fact IDs. The refresh button creates a new
mix; no recommendation service or account is required. Mobile navigation exposes
Discover, Encyclopedia, Database and More; the rest remain available in the menu.

Validation: `node tests/frontend.mjs`, `node tests/backend.mjs`, build and
`node scripts/validate-artifact.mjs`. The response check verifies decoded assets,
including the catalogue module and version index. These are JavaScript/HTTP
checks; no browser viewport or physical Android device test was available.

### v0.5 machine-readable publishing and early theme

Read-only publishing routes work on the same Worker as the app:

- `/facts` — linked HTML index; `/facts/{id}` — full fact HTML with canonical URL,
  language alternatives, visible source attribution and Article JSON-LD.
- `/entry/{id}` — reference description/history/tables rendered without JavaScript.
- `/developers` — human API guide and Dataset metadata.
- `/api/v1/facts?limit=100&offset=0` — paginated fact records with a next URL.
- `/api/v1/facts/all` — all filtered records; `?format=jsonl` for NDJSON.
- `/api/v1/facts/{id}`, `/api/v1/entries`, `/api/v1/taxonomy`, `/api/v1/versions`.
- `/openapi.json`, `/llms.txt`, `/robots.txt`, `/sitemap.xml`.

Search filters: `q`, `tag` (comma-separated AND), `topic`, `edition`, `version`,
`include_unverified=true`, `lang=en|es`. Development labels match exactly;
non-numeric ranges are not guessed. Read-only endpoints allow cross-origin GET,
HEAD and OPTIONS. Writes remain at the existing private submission/progress APIs.
No keys, reports, attachments or recovery-code records are published by these routes.
Current collection: 901 unique facts, including three newly edited historical facts.
Requests for more facts than exist return the actual count, without duplicates.
Raw datasets on the public GitHub repository also remain available for inspection.

The private ChatGPT preview cannot be indexed by public search crawlers. Publish
this Worker on a public Cloudflare origin without a sign-in/challenge to expose
these routes to crawlers. Canonical URLs, links, OpenAPI servers and sitemaps use
the request origin; no private preview domain is hardcoded in the publishing layer.
Submit `/sitemap.xml` in the domain owner's search-console account if desired.
The project has not submitted it or verified any search-console property.
These are retrieval/SEO foundations, not ranking tricks. `llms.txt` is an optional
reader guide, not a guaranteed search/ranking signal. No claim of priority,
indexing or AI citation is made. Preserve Wiki license/source attribution and
check separate image rights; API availability does not grant new reuse rights.

`web/theme.js` runs synchronously in the document head before the stylesheet and
before the fact fetch. It restores saved light/dark preferences, defaults to
system, sets the root background/color scheme immediately, and watches system
changes. The body and root palette agree before the main app renders. Android
also reports system night mode through its bridge. Existing choices remain saved;
Settings adds System (automatic), and the header cycles system/light/dark.

Added checks: `node tests/theme.mjs`, plus live Worker response tests for API
pagination/bulk data, CORS, private progress isolation, metadata and real HTML
content. Browser first-paint and physical Android tests remain unperformed.

### v0.6 Android system-bar fix

The APK now places its WebView inside a native FrameLayout. The container applies
system-bar, display-cutout and keyboard insets to its own padding, which measures
the actual WebView smaller. It forwards zeroed handled insets to Chromium so CSS
safe-area handling cannot count the same space twice. Insets continue to update
on keyboard hide, rotation, button navigation and gesture navigation. System-bar
icon contrast and the surrounding native background follow the web theme.
The website layout is unchanged by this Android-only fix.

Android instrumentation checks real on-screen WebView bounds against platform
insets, checks the HTML navigation bounds, opens/hides the keyboard, rotates the
activity, and captures screenshots. CI runs these on Android 15 and 16 with
three-button and gesture navigation. Reports are attached to the workflow run.
These emulator checks do not substitute for a physical Samsung device check.


## Version 0.7 — facts first, Android + Windows

The website root is the bilingual product/download page; `/app/` opens the fact feed.
Installed apps open the feed directly. The feed appends 24 facts at a time automatically,
keeps category-strip scroll position, and does not repeat cards within a mix. At the end
of the matching collection it offers a new mix rather than claiming unlimited unique facts.

`web/catalog-supplement.json` contains 20 curated legacy/Earth/Dungeons/Legends discoveries
and game edition definitions. The bundler and native asset scripts merge it into the
complete offline catalogue (921 facts). Keep base and supplement fact IDs unique.
New game edition version lists are intentionally empty until researched; exact missing
builds can still be entered and unknown applicability is labeled, never inferred as all versions.
Dungeons II uses explicit official supplemental sources pending a direct current Wiki review.

Windows: `npm ci --prefix desktop`, `node scripts/desktop-assets.mjs`, then
`npm run build --prefix desktop` on Windows. The Electron wrapper runs local content with
Node integration off, a sandboxed renderer, context isolation, restricted external links,
and a narrowly scoped update bridge. The installer is per-user and retains local data.
The Windows workflow builds and launches the packaged app for a fact-feed smoke check.

Apps check the repository's latest GitHub release on startup and periodically. A new
version presents an Update button linking to the corresponding official installer.
Android and Windows installation approval remains controlled by the operating system.
There is no silent installer, Play Protect bypass, or claim of verified developer status.
Stable Android updates require the same private release key for every release, and a
higher versionCode. Do not publish private keys, passwords, or debug APKs as stable updates.
The website only shows direct download links for assets actually present in the latest release.
