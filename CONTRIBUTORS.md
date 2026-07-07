<!-- Rose full repository refresh 2026-05-17 -->
# Contributors

Rose is strengthened by community contributions and review. The v2.0.0 buildout integrates or preserves the intent of five open upstream pull requests while adapting each change to the current codebase.

Rose is also inspired by the original [Ava WhatsApp Agent Course](https://github.com/neural-maze/ava-whatsapp-agent-course) from [neural-maze](https://github.com/neural-maze). [Miguel Otero Pedrido](https://github.com/MichaelisTrofficus) is credited here for the original Ava repository and full course video reference only. This source credit does not represent a direct Rose project contribution unless a direct Rose pull request or commit is present.

## Rose project contributors

| Contributor | Contribution |
|---|---|
| [@Alexi5000](https://github.com/Alexi5000) | Rose maintainer, product direction, full v2.0.0 buildout, v2.1.0 release metadata refresh, README stewardship, and repository-wide polish. |

## Source inspiration credits

| Source | Credit scope |
|---|---|
| [@MichaelisTrofficus](https://github.com/MichaelisTrofficus) | Original Ava repository and full course video reference that inspired Rose's companion direction. |
| [@copadoje](https://github.com/copadoje) | Ava course lineage and source inspiration for companion patterns. |

## Upstream pull request contributors

| Contributor | Pull request | Integrated intent |
|---|---:|---|
| [@a692570](https://github.com/a692570) | [#49](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/49) | Reduced sensitive WhatsApp response payload logging and added hygiene coverage against accidental raw payload logs. |
| [@rafaelgildin](https://github.com/rafaelgildin) | [#47](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/47) | Preserved Chainlit execution compatibility by keeping runtime entry points, startup guidance, and ignored generated artifacts aligned with the current codebase. |
| [@ysntns](https://github.com/ysntns) | [#46](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/46) | Added Chainlit translation artifacts to `.gitignore` so generated local files do not pollute commits. |
| [@TensorCruncher](https://github.com/TensorCruncher) | [#44](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/44) | Preserved assistant-role message construction semantics for generated image and scenario responses. |
| [@Shaheerabdullah1](https://github.com/Shaheerabdullah1) | [#43](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/43) | Updated deprecated Groq model defaults to current production-safe model names in configuration. |

Thank you to the Rose contributor and upstream community authors listed above, and to the original Ava creators for the source inspiration that helped shape Rose reliability, safety, developer experience, and product direction. This record intentionally avoids crediting non-human tooling as contributors.
