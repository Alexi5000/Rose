<!-- Rose full repository refresh 2026-05-17 -->
# Upstream Pull Request Integration

Rose manually ports the useful intent of five open upstream pull requests without applying stale patches to the evolved codebase. This preserves contributor value while avoiding unsafe lockfile rewrites and obsolete file paths.

| PR | Contributor | Integrated intent |
|---:|---|---|
| [#49](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/49) | [Abhishek Sharma, `a692570`](https://github.com/a692570) | Added repository hygiene coverage that prevents raw production `print()` calls and protects response payloads, headers, and tokens from accidental logging. |
| [#47](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/47) | [Rafael Gildin, `rafaelgildin`](https://github.com/rafaelgildin) | Preserved Chainlit execution compatibility and added safer local setup guidance for memory and artifact directories. |
| [#46](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/46) | [Yasin Tanış, `ysntns`](https://github.com/ysntns) | Kept broad `.chainlit/` coverage and explicitly documented generated translation ignores. |
| [#44](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/44) | [TensorCruncher](https://github.com/TensorCruncher) | Added graph-role coverage so generated assistant responses remain represented as assistant messages. |
| [#43](https://github.com/neural-maze/ava-whatsapp-agent-course/pull/43) | [Shaheer Abdullah, `Shaheerabdullah1`](https://github.com/Shaheerabdullah1) | Preserved deprecation-resistant Groq defaults and documented provider-model configuration. |

These changes align with Rose voice-first, stateful architecture while crediting the contributors who identified practical improvements upstream.
