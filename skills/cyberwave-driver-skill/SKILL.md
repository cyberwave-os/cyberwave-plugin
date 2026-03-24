---
name: cyberwave-driver
description: Scaffold a new Cyberwave-compatible driver. Use when the user wants to write, create, or build a driver for a hardware device on the Cyberwave platform.
argument-hint: [driver-name]
---

# Cyberwave Driver Scaffold

You are helping the user create a new **Cyberwave-compatible driver** — a Dockerized service that bridges a hardware device's native API and the Cyberwave platform via the digital twin model.

## Step 1 — Gather requirements

Ask the user the following questions **in a single message** before doing anything:

1. **Driver name** — what should the project folder and Python package be called? (e.g. `my-lidar-driver`)
2. **Hardware description** — one sentence about the device this driver will control or read from (e.g. "a SICK LiDAR over Ethernet using the SOPAS protocol")
3. **Asset registry ID** — the Cyberwave catalog asset this driver is for (e.g. `unitree/go2`, `cyberwave/standard-cam`). This is used to create a dev twin locally. If they don't have one yet, note it down as `unknown` and skip the local dev steps later.
4. **Author / organisation** — who is building this driver? (used in the LICENSE and README)
5. **SDK language** — Python or C++? (default: Python)
6. **Child twins?** — does this driver manage child twins (e.g. cameras attached to a robot)? yes/no

Wait for answers before proceeding to Step 2.

---

## Step 2 — Run the scaffold script

Once you have the answers, run `scaffold.py` (located in the same directory as this SKILL.md) using the `Bash` tool. The script generates the full project tree including all source files, Dockerfile, docker-compose, pyproject.toml, .env.example, .gitignore, .dockerignore, LICENSE, and README.

**Find `scaffold.py`** — it lives next to this SKILL.md file. Locate it with:
```bash
find ~ -name "scaffold.py" -path "*/cyberwave-driver-skill/*" 2>/dev/null | head -1
```

**Run it** with the flags that match the user's answers:
```bash
python /path/to/scaffold.py \
  --name "<driver-name>" \
  --description "<hardware description>" \
  --author "<author>" \
  --output-dir "." \
  [--child-twins]   # include only if user said yes
```

The script will print each created file and the next-steps checklist. Show that output to the user.

**Language choice.** If the user chose C++, inform them that the scaffold currently targets Python and offer to generate a `CMakeLists.txt`-based skeleton with the C++ SDK as a CMake FetchContent dependency. Ask them to confirm before proceeding.

---

## Step 3 — Orient the user in the generated code

After the script completes, give the user a short tour of the three files they will actually need to edit:

1. **`<package>/hardware.py`** — this is where all the hardware-specific work goes. `connect()` and `read_state()` are stubbed with `# TODO` markers. Point them here first.
2. **`<package>/driver.py`** — the main loop and twin sync logic. They should only need to touch this if they need to change polling frequency or handle commands.
3. **`Dockerfile`** — the `apt-get` line is commented out; if their hardware SDK requires system packages (e.g. `libusb`, `libudev`), they add them there.

---

## Step 4 — Set up local development environment

Skip this step if the user's registry ID is `unknown`.

Walk the user through getting the driver running locally against a real Cyberwave twin. Each sub-step below is a concrete command to run — guide them through it interactively, waiting for confirmation between steps where it makes sense.

### 4a — Install the Cyberwave CLI

```bash
pip install cyberwave
```

Tell the user this is the same CLI used to manage twins and edge devices. It will also write the `.env` file for them.

### 4b — Authenticate

```bash
cyberwave login
```

This opens a prompt for email and password and saves a workspace-scoped API token locally. Tell the user: if they're already logged in, this will confirm their session and they can skip it.

### 4c — Create a dev twin and write the `.env`

```bash
cyberwave twin create <registry-id> \
  --name "<driver-name>-dev" \
  --pair \
  --target-dir ./<driver-name>
```

Replace `<registry-id>` with the asset registry ID from Step 1 (e.g. `unitree/go2`), and `<driver-name>` with the project folder name.

What this does in one shot:
- Resolves the asset from the Cyberwave catalog
- Creates a new digital twin named `<driver-name>-dev`
- Registers this machine as an edge device (using a local device fingerprint)
- Pairs the twin to this edge device
- Writes a `.env` file directly into the driver project folder with `CYBERWAVE_TWIN_UUID`, `CYBERWAVE_API_KEY`, and any asset-specific fields

The user should select or create an environment when prompted (e.g. "Dev").

After this command succeeds, show the user what was written:
```bash
cat ./<driver-name>/.env
```

### 4d — Create the twin JSON stub

Edge Core normally provides the twin JSON file on disk. For local dev, create a minimal stub:

```bash
echo '{"metadata": {}}' > /tmp/cyberwave-twin.json
```

This is already the value set in `docker-compose.yml` for `CYBERWAVE_TWIN_JSON_FILE`.

### 4e — Build and run

```bash
cd <driver-name>
docker compose up --build
```

Tell the user what healthy startup logs should look like:
- `Hardware connected` — the hardware layer initialized (stub will always succeed until they implement it)
- `Driver running (twin=<uuid>)` — the main loop started
- No `ERROR` or `sys.exit(1)` lines

If they see an exit with a non-zero code, it means `hardware.py`'s `connect()` raised — this is expected if they haven't implemented it yet and the hardware isn't available.

### 4f — Invite iteration

Tell the user:

> The driver is now running against a real twin in Cyberwave. Open the Cyberwave dashboard and navigate to the twin — you should see it listed as connected. As you implement `hardware.py` and the driver writes state via `_update_twin_state()`, those values will appear in the twin's metadata in the dashboard.
>
> The inner loop is: edit `hardware.py` → `docker compose up --build` → check logs and dashboard.

---

## Step 5 — Offer to help with the hardware layer

Ask the user: *"Do you want me to help implement `hardware.py` for your specific device?"*

If yes, ask them for:
- The hardware SDK name or protocol (e.g. `pyserial`, `pymodbus`, a vendor SDK)
- The connection parameters (IP address / port, serial port, baud rate, etc.) — or note that these should come from `edge_configs` if they vary per device

Then implement `hardware.py` with real SDK calls, replacing the stubs. Make sure to:
- Import only what is needed; add the SDK to `requirements.txt`
- Exit with a non-zero code (raise an exception) in `connect()` if the device is unreachable, so Edge Core can restart the driver
- Return a flat dict of state fields from `read_state()` (these become twin metadata)

---

## Notes for Claude

- **Non-zero exit on hardware failure is non-negotiable.** Edge Core detects startup failures via exit code. Never swallow unrecoverable exceptions.
- **`CYBERWAVE_TWIN_JSON_FILE` is the config source of truth.** `metadata.edge_configs` holds per-device settings. Do not hardcode addresses or credentials in the image.
- **Keep hardware concerns in `hardware.py`.** `driver.py` must never import the hardware SDK directly — the abstraction boundary makes it easy to mock in tests.
- **`scaffold.py` is idempotent per name but not overwrite-safe** — it will refuse to run if the output directory already exists, so the user can re-run safely with a different name.
