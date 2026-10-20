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
