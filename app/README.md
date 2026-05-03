# Drum Sheet Manager App

TypeScript + React app for the Drum Sheet Manager backend.

## Requirements

- Node.js 20+
- npm
- Backend API running (default: http://127.0.0.1:8000)

## Install

```bash
npm install
```

## OpenAPI Sync

The app updates its API schema and generated types from the backend OpenAPI spec.

```bash
npm run openapi:update
```

This command:

1. Fetches `BACKEND_OPENAPI_URL` (default `http://127.0.0.1:8000/openapi.json`)
2. Writes `src/generated/openapi.json`
3. Regenerates `src/generated/openapi-types.ts`

## Run

```bash
npm run dev
```

`dev` automatically runs `openapi:update` before Vite starts.

## Build

```bash
npm run build
```

`build` also runs `openapi:update` first so schema updates propagate into the production build.
