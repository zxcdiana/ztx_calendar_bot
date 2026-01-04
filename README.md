
# Installation
1. Create `.env` file (see: `.env.example`)
2. Run bot:
```bash
uv run -m app
```

# Docker installation
1. Make step 1 from the **Installation** block
2. Build image:
```bash
docker build -t ztx_calendar_bot .
```
3. Create and run container:
```bash
docker run \
    --env-file=".env" \
    --name="calendar_bot" \
    --restart=unless-stopped \
    -d \
    ztx_calendar_bot
```
4. Check logs:
```bash
docker logs -f calendar_bot
```
<details>
    <summary>Steps 2, 3, 4 in one-command</summary>

```bash
docker build -t ztx_calendar_bot . && \
echo Image builded
docker run --env-file=".env" --name="calendar_bot" --restart=unless-stopped -d ztx_calendar_bot && \
echo Container started && \
docker logs -f calendar_bot
```
</details>

<details>
    <summary>Uninstall</summary>

```bash
docker rm -f calendar_bot && \
docker rmi ztx_calendar_bot
```
</details>
