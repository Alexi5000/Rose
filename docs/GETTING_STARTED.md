# 1. Clone the repository

First thing first, clone the repository.

```bash
git clone https://github.com/neural-maze/ava-whatsapp-agent-course.git
cd ava-whatsapp-agent-course
```

# 2. Install uv

Instead of `pip` or `poetry`, we are using `uv` as the Python package manager. 

To install uv, simply follow these [instructions](https://docs.astral.sh/uv/getting-started/installation/). 

# 3. Install the project dependencies

Once uv is installed, you can install the project dependencies:

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend
npm install
cd ..
```

Just to make sure that everything is working, simply run the following command:

```bash
uv run python --version
```

The Python version should be `Python 3.12.8` or higher.


# 4. Environment Variables

Now that all the dependencies are installed, it's time to populate the `.env` file with the correct values.
To help you with this, we have created a `.env.example` file that you can use as a template.

```
cp .env.example .env
```

Now, you can open the `.env` file with your favorite text editor and set the correct values for the variables.
You'll notice there are a lot of variables that need to be set.

```
GROQ_API_KEY=""

ELEVENLABS_API_KEY=""
ELEVENLABS_VOICE_ID=""

TOGETHER_API_KEY=""

QDRANT_URL=""
QDRANT_API_KEY=""

WHATSAPP_PHONE_NUMBER_ID = ""
WHATSAPP_TOKEN = ""
WHATSAPP_VERIFY_TOKEN = ""
```

In this doc, we will show you how to get the values for all of these variables, except for the WhatsApp ones. 
That's something we will cover in a dedicated lesson, so don't worry about it for now, **you can leave the WhatsApp variables empty**.

### Groq

To create the GROQ_API_KEY, and be able to interact with Groq models, you just need to follow this [instructions](https://console.groq.com/docs/quickstart).

![alt text](img/groq_api_key.png)

Once you have created the API key, you can copy it and paste it into an `.env` file (following the same format as the `.env.example` file).

### ElevenLabs

To create the ELEVENLABS_API_KEY you need to create an account in [ElevenLabs](https://elevenlabs.io/). After that, go to your account settings and create the API key.

![alt text](img/elevenlabs_api_key.png)

As for the voice ID, you can check the available voices and select the one you prefer! We'll cover this in a dedicated lesson.

### Together AI

Log in to [Together AI](https://www.together.ai/) and, inside your account settings, create the API key.

![alt text](img/together_api_key.png)

As we did with the previous API keys, copy the value and paste it into your own `.env` file.

### Qdrant

This project uses Qdrant both locally (you don't need to do anything) and in the cloud (you need to create an account in [Qdrant Cloud](https://login.cloud.qdrant.io/)).

Once you are inside the Qdrant Cloud dashboard, create your API key here:

![alt text](img/qdrant_api_key.png)

You also need a QDRANT_URL, which is the URL of your Qdrant Cloud instance. You can find it here:

![alt text](img/qdrant_url.png)

Copy both values and paste them into your own `.env` file.

**This is everything you need to get the project up and running.**

# 5. First run

Once you have everything set up, it's time to run the project locally. This is the best way to check that everything is working.

## Running Rose (Voice-First Web Interface)

Rose now uses a modern voice-first web interface instead of Chainlit. To start the application:

### Development Mode (Recommended)

Start both frontend and backend with hot reload:

```bash
python scripts/run_dev_server.py
```

This starts:
- 🎨 **Frontend**: http://localhost:3000 (Vite dev server with hot reload)
- 🔌 **Backend**: http://localhost:8000 (FastAPI with auto-reload)
- 📚 **API Docs**: http://localhost:8000/api/v1/docs (Swagger UI)

Open http://localhost:3000 in your browser to interact with Rose through the voice interface.

### Production Mode

Build and serve the production version:

```bash
python scripts/build_and_serve.py
```

This builds the frontend and serves it at http://localhost:8000

## Using the Voice Interface

1. Click and hold the voice button to start recording
2. Speak your message while holding the button
3. Release to send your message to Rose
4. Rose will respond with both text and audio

## Alternative: Docker Compose (Legacy)

If you prefer to use Docker Compose with the Chainlit interface (legacy):

```bash
make ava-run
```

This starts:
* A Qdrant Database (http://localhost:6333/dashboard)
* A Chainlit interface (http://localhost:8000)
* A FastAPI application (http://localhost:8000/api/v1/docs)

> **Note**: The Docker Compose setup uses the older Chainlit interface. For the modern voice-first experience, use the development server method above.

To clean up the Docker Compose application:

```bash
make ava-delete
```

For more information, check the [Makefile](../Makefile).

## Troubleshooting

If you encounter issues, see [DEVELOPMENT.md](../DEVELOPMENT.md) for detailed troubleshooting steps.
