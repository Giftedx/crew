# Ultimate Discord Intelligence Bot Crew

Welcome to the Ultimate Discord Intelligence Bot project, powered by [crewAI](https://crewai.com). This template helps you set up a multi-agent AI system using crewAI so agents can collaborate on complex tasks and maximize their collective intelligence.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```

Copy `.env.example` to `.env` and fill in the required secrets:

```bash
cp .env.example .env
# edit .env and add your API keys
```

All paths and credentials are configured through environment variables so the project
works across Linux, macOS and Windows without modification.
Key variables include `CREWAI_BASE_DIR` (defaulting to a `crew_data` folder in your
home directory) and optional overrides like `CREWAI_DOWNLOADS_DIR` or
`CREWAI_YTDLP_CONFIG` for custom locations. The repository ships with a default
yt-dlp configuration under `yt-dlp/config/crewai-system.conf` and supports
downloading from YouTube, Twitch, Kick, Instagram and X/Twitter. The pipeline automatically
selects the appropriate downloader based on the URL. When providing a Discord
webhook via `DISCORD_WEBHOOK` ensure it is a public HTTPS URL; local or private
IP addresses are rejected for safety. A separate `DISCORD_PRIVATE_WEBHOOK` can
be supplied to the internal `Discord Private Alert Tool` for system health
notifications. Pair this with the `System Status Tool` and the `monitor_system`
task to include CPU load and disk usage metrics in those alerts.
Optional API keys can further enhance fact-checking: set `SERPLY_API_KEY`,
`EXA_API_KEY`, `PERPLEXITY_API_KEY`, and `WOLFRAM_ALPHA_APPID` to enable
additional search backends used by the Fact Check Tool.
The accompanying `Multi-Platform Monitor Tool` keeps an in-memory record of
seen items and reports only fresh content so downloads are triggered once per
upload. Dedicated monitors for X and Discord expose structured metadata for new
posts, paving the way for richer context gathering.
To broaden analysis beyond video content, the repository ships lightweight
tools for gathering social-media chatter and scoring factual accuracy. The
`Social Media Monitor Tool` aggregates Reddit, X and Discord posts matching a
keyword, while the `Truth Scoring Tool` converts fact-check verdicts into a
numerical trustworthiness score.  Building on those verdicts, the
`Trustworthiness Tracker Tool` maintains per-person counts of truthful and
false statements to derive long-term reliability profiles that feed the
overall scoreboard.  For clip context
checks, the `Transcript Index Tool` slices transcripts into timestamped
chunks so the `Context Verification Tool` can compare quoted clips against the
surrounding transcript.  Claims can be probed via the lightweight `Fact Check
Tool`, and cumulative lie or misquote counts are persisted by the
`Leaderboard Tool`.  A `Steelman Argument Tool` combines supporting snippets to
produce the strongest possible version of a claim for deep-dive reasoning.
These pieces power the informal H3/Hasan debate analysis
flow: VODs are indexed, clip context verified, claims fact-checked and a
scoreboard of lies, misquotes and misinfo is exposed through Discord commands
like `/analyze`, `/context`, `/claim`, `/leaderboard`, `/timeline` and `/ask`.
Two partisan defenders – Traitor AB for Ethan and Old Dan for Hasan – generate
short, casual closing statements for each analysis.  The `/timeline` command
surfaces a chronological list of analysed clips for a video while `/ask`
queries the stored vector memory to surface relevant transcript or analysis
snippets for quick Q&A.  A `/profile` command summarises per-person trust
metrics and recent events collected throughout debates.
For long-term memory the pipeline can connect to a Qdrant vector database using
`QDRANT_URL` and optional `QDRANT_API_KEY`.  Raw transcripts are written to a
`transcripts` collection while distilled analysis summaries land in an
`analysis` collection, keeping sources and reasoning separate for retrieval.
For audio transcription you can choose the Whisper model size by setting
`WHISPER_MODEL` (defaults to `base`). The text analysis component relies on NLTK
corpora which are downloaded automatically on first use.
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Update `src/ultimate_discord_intelligence_bot/config/agents.yaml` to define agents
  (a single `content_manager` is provided as an example)
- Adjust `src/ultimate_discord_intelligence_bot/config/tasks.yaml` to describe your
  tasks and required inputs
- Extend `src/ultimate_discord_intelligence_bot/crew.py` if you need additional
  logic or tools
- Modify `src/ultimate_discord_intelligence_bot/main.py` to change how inputs are
  supplied when running locally

## Running the Project

To run the default crew against a specific video, supply the URL as input:

```bash
crewai run --inputs url=<video_url>
```

You can also invoke the pipeline directly without the crew layer:

```bash
python src/ultimate_discord_intelligence_bot/pipeline.py <video_url>
```

Both approaches download the video, upload it to Google Drive, analyse the
transcript, gather cross-platform discussions, flag basic logical fallacies,
synthesise perspectives, score claim truthfulness and post a summary to
Discord.
Additionally, transcripts and analysis metadata are stored in dedicated Qdrant
collections so future agents can perform retrieval-augmented generation over
the processed content.

## Understanding Your Crew

The Ultimate Discord Intelligence Bot crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Future Work

- Introduce a **Personality Synthesis Manager** agent that learns from user interactions in Q&A threads to adapt the bot's conversational style over time.

## Support

For support, questions, or feedback regarding the Ultimate Discord Intelligence Bot crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
