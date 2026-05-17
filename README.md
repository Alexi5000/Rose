<p align="center">
  <a href="https://github.com/Alexi5000/Rose">
    <img src="assets/rose-header.svg" alt="Rose" width="100%" />
  </a>
</p>

<h1 align="center">Rose</h1>

<p align="center">
  <strong>A voice-first AI companion for calm, reflective, and emotionally aware conversations.</strong>
</p>

<p align="center">
  <a href="#start">Start</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/Alexi5000/Rose/releases/tag/v2.0.0">Release</a>
  &nbsp;·&nbsp;
  <a href="docs/ARCHITECTURE_PATTERNS.md">Design Notes</a>
  &nbsp;·&nbsp;
  <a href="CONTRIBUTORS.md">Contributors</a>
  &nbsp;·&nbsp;
  <a href="LICENSE">License</a>
</p>

Rose is an open-source wellness companion designed around the simple act of speaking and being heard. It listens, understands the shape of the conversation, remembers what matters, and responds with a calm voice or clear text.

The project is intentionally warm on the surface and carefully structured underneath. Rose keeps the strongest design ideas from the Ava companion lineage, including a voice-first interaction loop, durable memory, multimodal awareness, and clean boundaries between the conversation experience and the intelligence services behind it.

## Why Rose

| Experience | What it means |
|---|---|
| **Speak naturally** | Rose is built for voice-led sessions instead of form-driven chat. |
| **Feel continuity** | Important context can be carried forward so conversations do not feel disposable. |
| **Stay grounded** | The assistant is shaped for grief support, reflection, emotional processing, and gentle wellness conversations. |
| **Use multiple modes** | Text, audio, and richer companion workflows can live in the same experience. |
| **Keep it adaptable** | The project can evolve across models, voice providers, and interfaces without losing its core companion pattern. |

## The companion loop

<p align="center">
  <a href="docs/ARCHITECTURE_PATTERNS.md">
    <img src="assets/rose-architecture.svg" alt="Rose companion loop" width="100%" />
  </a>
</p>

Rose follows a human-centered loop: listen, understand, remember, and respond. The interface stays focused on the person speaking. The deeper orchestration, memory, and provider choices stay behind the scenes, where they can be improved without cluttering the product experience.

## Start

Clone the project and create your local environment.

```bash
git clone https://github.com/Alexi5000/Rose.git
cd Rose
cp .env.example .env
uv sync --extra test
cd frontend && npm install && cd ..
```

Add your provider keys to `.env`, then run Rose locally.

```bash
uv run uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port 8000 --reload
cd frontend && npm run dev
```

Open `http://localhost:5173` and start a voice session.

## Documentation

| Resource | Purpose |
|---|---|
| [Design notes](docs/ARCHITECTURE_PATTERNS.md) | How the original companion patterns are preserved in Rose. |
| [Release notes](docs/RELEASE_NOTES_v2.md) | What changed in the v2.0.0 buildout. |
| [Deployment guide](docs/DEPLOYMENT.md) | How to run Rose outside a local development setup. |
| [Memory system](docs/MEMORY_SYSTEM.md) | How long-term context and recall are organized. |
| [Contributing](CONTRIBUTING.md) | How to propose changes without breaking the companion model. |

## Community

Rose includes integrated work and guidance from community pull requests in the original Ava course repository. Those contributions are credited in [CONTRIBUTORS.md](CONTRIBUTORS.md) and documented in [the integration notes](docs/UPSTREAM_PR_INTEGRATION.md).

## License

Rose is released under the [MIT License](LICENSE).

<p align="center">
  <sub>Maintained by <a href="https://github.com/Alexi5000">Alexi5000</a>. Originally created from the Ava companion course lineage by <a href="https://github.com/neural-maze">neural-maze</a>.</sub>
</p>
