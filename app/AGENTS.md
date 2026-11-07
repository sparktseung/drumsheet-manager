# Frontend — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — repo root
> **Deeper**: [src/AGENTS.md](src/AGENTS.md) — frontend source

## Stack
- React 19, TypeScript 5.9, Vite 8
- react-router-dom v7, react-pdf v10
- `verbatimModuleSyntax`, `noUnusedLocals`, `noUnusedParameters`

## Structure

```
app/
├── src/
│   ├── api/            # API client (fetch wrappers, type re-exports)
│   ├── components/     # Reusable UI components
│   ├── hooks/          # Custom React hooks
│   ├── pages/          # Route-level page components
│   ├── generated/      # Auto-generated OpenAPI types + spec
│   ├── App.tsx         # Root component (song list, search, pagination)
│   ├── main.tsx        # Entry point, BrowserRouter + routes
│   └── index.css       # Global styles
├── scripts/            # update-openapi.mjs (fetches OpenAPI spec)
├── package.json
├── vite.config.ts
├── tsconfig.json
└── eslint.config.js
```

## Commands
```bash
npm install
npm run dev          # fetches OpenAPI types, then starts Vite (:5173)
npm run build        # fetches OpenAPI types, typechecks, builds
npm run lint         # eslint
```

## Key patterns

- **OpenAPI types**: `npm run dev`/`build` auto-fetch from `BACKEND_OPENAPI_URL` (default `http://localhost:8000/openapi.json`). Backend must be running.
- **API client** (`src/api/client.ts`): All backend calls go through `requestJson<T>()` which adds JSON headers and throws on non-OK responses.
- **Routing**: Two routes — `/` (App, song list) and `/songs/:songId` (SongDetailPage, viewer).
- **State**: No global state library. Each page/hook manages its own state with `useState`/`useEffect`.
- **`.env`**: Vite loads from repo root (`envDir: '..'`). Use `VITE_` prefix for client-exposed vars.
- **react-pdf**: `pdfjs-dist` worker loaded from `import.meta.url` — no extra config needed.