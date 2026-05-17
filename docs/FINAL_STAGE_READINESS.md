<!-- Rose full repository refresh 2026-05-17 -->
# Final Stage Readiness

Rose has been prepared for a final review stage after a controlled full-repository refresh. The refresh is intended to make the repository visibly current across every tracked file while preserving the latest upstream base, the simplified product README, contributor credit, release notes, and the recovered Rose buildout work.

## Repository posture

| Area | Final-stage expectation |
|---|---|
| Upstream alignment | The branch should remain based on the latest original upstream state, with Rose changes replayed on top. |
| File coverage | Every tracked file should be included in the final refresh commit so GitHub records a repository-wide update. |
| README | The root README should remain concise, product-forward, free of badge or workflow clutter, and visibly link the Ava full course image reference. |
| Credits | The README and contributor documentation should credit Alex as the Rose project contributor, and should credit Miguel Otero Pedrido only for the original Ava repository and full course video reference unless a direct Rose contribution exists. |
| Quality | The repository should pass targeted checks for conflict markers, no em dashes, README resolution, link presence, and syntax safety. |
| Release | The v2.0.0 release target should be refreshed only after the final branch state is pushed successfully. |

## Final checks

Before the final stage is considered ready, the repository should confirm that the working tree is clean after commit, all tracked files were changed by the refresh, the root `README.md` is the GitHub-visible README, `.github/README.md` is absent, and the branch is published to `origin/main`.

## Credit note

Rose is inspired by the original [Ava WhatsApp Agent Course](https://github.com/neural-maze/ava-whatsapp-agent-course) from [neural-maze](https://github.com/neural-maze). The README should keep the [Ava full course image](../img/video_thumbnails/ava_full_course.png) visible as a linked course reference. `CONTRIBUTORS.md` should list [Alex](https://github.com/Alexi5000) as the Rose project contributor, should credit [Miguel Otero Pedrido](https://github.com/MichaelisTrofficus) only for the original Ava repository and full course video reference, and should avoid adding non-human tooling names as contributors.
