# Rose v2.1.0 Release Notes

Rose v2.1.0 is a release metadata, public identity, and documentation consistency release. It keeps the existing provider behavior intact while making the repository present itself as a polished voice-first AI emotional support companion.

## Highlights

| Theme | Release impact |
|---|---|
| Public About surface | GitHub About, README language, API titles, tests, and docs now use current Rose Voice Companion positioning. |
| Version consistency | Python package metadata, uv lock metadata, frontend package metadata, OpenAPI metadata, health responses, monitoring release fallback, and production examples now align on `2.1.0`. |
| API clarity | Documentation now separates the app release version from the stable `/api/v1` route namespace. |
| Frontend polish | The browser tab title now reads `Rose` instead of the scaffold placeholder. |
| Safety positioning | Public wording continues to frame Rose as AI emotional support, not therapy, diagnosis, professional care, or emergency help. |

## Upgrade Notes

No public API, route, schema, provider name, or required environment variable changed in this release.

Set `APP_VERSION=2.1.0` in production environments when you want monitoring tools such as Sentry to group events under this release. The default app settings and `.env.example` already use `2.1.0`.

## Validation

The release was prepared after local source, docs, package metadata, and GitHub repository metadata cleanup. CI should be green on `main` before publishing the GitHub release.
