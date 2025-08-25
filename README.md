# UltimateDiscordIntelligenceBotCompleteSocialMediaAnalysisFactCheckingSystem Crew

Welcome to the UltimateDiscordIntelligenceBotCompleteSocialMediaAnalysisFactCheckingSystem Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

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
Key variables include `CREWAI_BASE_DIR` (defaulting to a `CrewAI_Content_System`
folder in your home directory) and optional overrides like `CREWAI_DOWNLOADS_DIR`
or `CREWAI_YTDLP_CONFIG` when custom locations are required.
For audio transcription you can choose the Whisper model size by setting
`WHISPER_MODEL` (defaults to `base`). The text analysis component relies on NLTK
corpora which are downloaded automatically on first use.
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system/config/agents.yaml` to define your agents
- Modify `src/ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system/config/tasks.yaml` to define your tasks
- Modify `src/ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system/crew.py` to add your own logic, tools and specific args
- Modify `src/ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

To execute the end-to-end content pipeline for a single YouTube URL:

```bash
python src/Ultimate\ Discord\ Intelligence\ Bot\ -\ Complete\ Social\ Media\ Analysis\ \&\ Fact-Checking\ System/pipeline.py <video_url>
```

This command initializes the ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the UltimateDiscordIntelligenceBotCompleteSocialMediaAnalysisFactCheckingSystem Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
