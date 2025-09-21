# Curated Resources Index

This index groups external resources useful for advancing our Discord bot, Activities, LLM inference, RL evaluation, and library choices.

## Discord Bot Frameworks

- Official

  - [discord developers](https://discord.com/developers)
  - [discord-interactions-python](https://github.com/discord/discord-interactions-python)
- Community SDKs

  - discord.py: [github.com/Rapptz/discord.py](https://github.com/Rapptz/discord.py)
  - disnake: [github.com/DisnakeDev/disnake](https://github.com/DisnakeDev/disnake)
  - hikari: [github.com/hikari-py/hikari](https://github.com/hikari-py/hikari)
  - interactions.py: [github.com/interactions-py/interactions.py](https://github.com/interactions-py/interactions.py)
  - nextcord: [github.com/nextcord/nextcord](https://github.com/nextcord/nextcord)
  - pycord: [github.com/Pycord-Development/pycord](https://github.com/Pycord-Development/pycord)
  - discord-interactions.py: [github.com/LiBa001/discord-interactions.py](https://github.com/LiBa001/discord-interactions.py)
  - dispike: [github.com/ms7m/dispike](https://github.com/ms7m/dispike)
  - flask-discord-interactions: [github.com/breqdev/flask-discord-interactions](https://github.com/breqdev/flask-discord-interactions)

Permissions & Intents

- Calculator: [tools.botforge.org/permissions](https://tools.botforge.org/permissions)
- Intent matrix: [ziad87.net/intents](https://ziad87.net/intents/)

Embeds & Networking

- Embed previewer: [github.com/JohnyTheCarrot/discord-embed-previewer](https://github.com/JohnyTheCarrot/discord-embed-previewer)
- Hourai Networking: [github.com/HouraiTeahouse/HouraiNetworking](https://github.com/HouraiTeahouse/HouraiNetworking)

## Discord Activities (Embedded Apps)

- Core concepts: <https://discord.com/developers/docs/discord-social-sdk/core-concepts>
- Getting started: <https://discord.com/developers/docs/discord-social-sdk/getting-started>
- Development guides: <https://discord.com/developers/docs/activities/development-guides>
- Building an Activity: <https://discord.com/developers/docs/activities/building-an-activity>

Local development:

- Run locally: <https://discord.com/developers/docs/activities/development-guides/local-development#run-your-application-locally>
- Launch from client: <https://discord.com/developers/docs/activities/development-guides/local-development#launch-your-application-from-the-discord-client>
- URL mapping: <https://discord.com/developers/docs/activities/development-guides/local-development#url-mapping>
- Logging: <https://discord.com/developers/docs/activities/development-guides/local-development#logging>
- User actions: <https://discord.com/developers/docs/activities/development-guides/user-actions#setting-up-an-entry-point-command>
- Open external link: <https://discord.com/developers/docs/activities/development-guides/user-actions#open-external-link>
- Invite dialog: <https://discord.com/developers/docs/activities/development-guides/user-actions#open-invite-dialog>
- Share moment: <https://discord.com/developers/docs/activities/development-guides/user-actions#open-share-moment-dialog>
- Encourage hardware acceleration: <https://discord.com/developers/docs/activities/development-guides/user-actions#encourage-hardware-acceleration>

SDK & Examples

- Embedded App SDK: [github.com/discord/embedded-app-sdk](https://github.com/discord/embedded-app-sdk)
- Examples: [github.com/discord/embedded-app-sdk-examples](https://github.com/discord/embedded-app-sdk-examples)
- Getting started Activity: [github.com/discord/getting-started-activity](https://github.com/discord/getting-started-activity)

Local guide in this repo: see [activities_local_dev.md](activities_local_dev.md) for a concise local setup walkthrough.

Local tooling

- Node.js: <https://nodejs.org/en>
- Express: <https://expressjs.com/>
- Vite: <https://vite.dev/>
- Cloudflared (tunnel): <https://github.com/cloudflare/cloudflared?tab=readme-ov-file#installing-cloudflared>

## LLM Inference & Acceleration

- vLLM docs: <https://docs.vllm.ai/en/latest/>
- Anyscale continuous batching: <https://www.anyscale.com/blog/continuous-batching-llm-inference>
- NVIDIA Dynamo: <https://developer.nvidia.com/dynamo>

Recommended path

- Start with vLLM for server-side generation; enable continuous batching for throughput.
- Evaluate GPU availability; consider inference server + client integration from the bot.

## RL & Evaluation

- TensorFlow Actor-Critic tutorial: <https://www.tensorflow.org/tutorials/reinforcement_learning/actor_critic>
- Arize LLM evaluation: <https://arize.com/llm-evaluation/>

Suggested plan

- Use offline eval harness (already present) to record trajectories.
- Define reward proxies (latency, correctness signals) and iterate with bandits before full RL.

## Inspiration & References

- llmcord (Discord LLM): [github.com/jakobdylanc/llmcord](https://github.com/jakobdylanc/llmcord)
- Clone your Discord friends (article): <https://pixelmelt.substack.com/p/clone-your-discord-friends?utm_medium=web>

---

See also:

- Activities health endpoint: `/activities/health` (added for local testing)
- Our API server: `src/server/app.py`
