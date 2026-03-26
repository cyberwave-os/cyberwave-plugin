---
name: cyberwave
description: Develop a Physical AI application with Cyberwave. Use when the user wants to write, build, or prototype an application that controls robots, reads sensors, manages digital twins, or streams video using the Cyberwave platform.
argument-hint: [what you want to build]
---

# Cyberwave Application Development

You are helping the user build a **Physical AI application** on the Cyberwave platform — software that connects to robots and sensors, manages digital twins, and optionally runs simulation or teleoperation workflows.

## Step 0 — Set up the Cyberwave environment

Before writing any code, the user needs a virtual environment in Cyberwave that mirrors their real-world setup — the robots they have, the cameras, the layout.

Ask the user in a single message:

> "Before we write any code, let's set up your Cyberwave environment so it mirrors your physical setup.
>
> - What robots do you have? (e.g. SO101 arm, Unitree Go2 — or I can show you the catalog)
> - Do you have any cameras or sensors to add?
> - Do you already have an environment and digital twins set up in Cyberwave, or are we starting from scratch?"

Wait for their answer, then proceed as follows.

### If the Cyberwave MCP tools are available in this session

The cyberwave plugin ships with an MCP server that is automatically configured when the plugin is installed. If it is active, you will have tools from the `cyberwave` MCP server available (e.g. to search the catalog, create environments, add twins). Use them to:

- Create an environment if the user doesn't have one
- Search the asset catalog for the robots and sensors they mention
- Add the matching digital twins to the environment and position them

Once the environment is ready, move on to Step 1.

### If the Cyberwave MCP tools are NOT available in this session

Do not assume the MCP is available. If the tools are absent, offer the user two options:

**Option A — Enable the MCP (recommended):**

Tell the user that the Cyberwave MCP server lets Claude set up their environment directly from the chat. To enable it, add the following to `.mcp.json` in the project root (or `~/.claude/.mcp.json` for global access), then restart Claude Code:

```json
{
  "mcpServers": {
    "cyberwave": {
      "url": "https://mcp.cyberwave.com/mcp",
      "headers": {
        "Authorization": "Bearer ${CYBERWAVE_API_KEY}"
      }
    }
  }
}
```

Set `CYBERWAVE_API_KEY` to their API token from Dashboard → Profile → API Tokens.

**Option B — Set up manually in the dashboard:**

Guide the user to do it themselves:

1. Go to the Cyberwave dashboard and click **New Environment** — give it a name
2. Inside the environment, click **Add from Catalog** and search for their robot
3. Add and position their digital twins

Once either option is complete, confirm the environment is ready and move on to Step 1.

---

## Step 1 — Choose an interface

Ask the user which interface they want to use, in a single message:

> "Which interface would you like to use to build your Cyberwave application?
>
> 1. **Python SDK** (recommended) — high-level client that wraps REST and MQTT; best for most applications
> 2. **C++ SDK** — low-level SDK for performance-critical or embedded use cases
> 3. **APIs directly** — raw REST (HTTPS) and MQTT access; use when you need a non-Python language or fine-grained control
>
> What would you also like to build? (e.g. control a robot arm, stream camera video, trigger a workflow)"

Wait for the answer, then follow the matching section below.

---

## Path A — Python SDK

### A1 — What kind of application?

Before walking through the SDK, ask the user one follow-up question:

> "Are you building a **remote application** — code that runs on your machine (or any server) and controls robots over the network — or an **on-device application** — code that runs directly on the robot's hardware and interacts with local cameras and sensors?"

Wait for the answer, then follow **Path A-Remote** or **Path A-Edge** below. Both start with the same setup steps.

---

### Shared setup (both paths)

**Requirements:**

- Python 3.11+
- A Cyberwave API token — generate one at [Dashboard → Profile → API Tokens](https://cyberwave.com/profile)

**Install:**

```bash
pip install cyberwave
```

**Set your API token:**

```bash
export CYBERWAVE_API_TOKEN="your_token_here"
```

**Initialize the client:**

```python
from cyberwave import Cyberwave

cw = Cyberwave()  # reads CYBERWAVE_API_TOKEN from environment
```

**Simulation vs live** — control where commands are sent:

```python
cw = Cyberwave(mode="simulation")  # safe for development
cw.affect("simulation")            # subsequent commands target the digital twin
# cw.affect("live")               # switch to physical robot when ready
```

Individual calls can still override the target with an explicit `source_type` argument.

---

### Path A-Remote — Application running on any machine

This path covers applications that connect to robots over the network via the Cyberwave cloud: dashboards, automation scripts, AI pipelines, teleoperation UIs, etc.

#### AR1 — Connect to a twin

```python
# By asset registry ID (most common)
robot = cw.twin("the-robot-studio/so101")

# By twin UUID
robot = cw.twin(twin_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
```

#### AR2 — Edit the twin's position, rotation and scale in the environment

```python
robot.edit_position(x=1.0, y=0.0, z=0.5)   # metres
robot.edit_rotation(yaw=90)                  # degrees
robot.edit_scale(x=1.0, y=1.0, z=1.0)
```

#### AR3 — Move the robot in sim or real world

```python
cw.affect("simulation")   # or "real-world" for the physical robot
rover = cw.twin("unitree/go2")
rover.move_forward(distance=1.0)
rover.turn_left(angle=1.57)

# Same approach for articulated robots (arms, etc.)
robot = cw.twin("the-robot-studio/so101")
robot.joints.set("shoulder_joint", 45, degrees=True)
robot.joints.set("elbow_joint", 1.57, degrees=False)  # radians
```

#### AR4 — Read joint state

```python
joints = robot.joints.list()
value  = robot.joints.get("shoulder_joint")
all_states = robot.joints.get_all()
```

#### AR5 — Capture a frame from the robot's camera

Frames are pulled via the Cyberwave cloud — the application does not need to be co-located with the hardware.

```python
path   = robot.capture_frame()                         # save JPEG, return path
frame  = robot.capture_frame("numpy")                  # BGR NumPy array (OpenCV)
image  = robot.capture_frame("pil")                    # PIL.Image
frames = robot.capture_frames(count=10, interval_ms=100)  # burst
```

#### AR6 — Workflows

```python
workflows = cw.workflows.list()

run = cw.workflows.trigger(
    uuid="workflow-uuid",
    inputs={"speed": 1.0, "target": "home"}
)
run.wait(timeout=60)

runs = cw.workflow_runs.list(workflow_id="workflow-uuid", status="completed")
```

#### AR7 — Asset and environment management

```python
results = cw.assets.search("lidar")
asset   = cw.assets.create(name="my-sensor", description="Custom sensor")
cw.assets.upload_glb(asset.uuid, "/path/to/model.glb")

workspaces = cw.workspaces.list()
project    = cw.projects.create(name="Demo", description="…", workspace_id=ws.uuid)
env        = cw.environments.create(name="Dev", description="…", project_id=project.uuid)
snapshot   = cw.environments.create_preview(env.uuid)
```

#### AR8 — Offer to help build

Ask the user:

> "What would you like to implement first? I can help you write the control loop, integrate a vision pipeline with captured frames, set up simulation testing, or wire up a workflow trigger."

---

### Path A-Edge — Application running on the robot's hardware

This path covers applications that run **on the same machine as the robot** and interact directly with local hardware: vision pipelines that process the camera feed in real time, monitoring services that raise alerts, or any application that needs low-latency access to sensors.

> **Note for Claude:** if the user wants to write a driver that bridges new hardware to Cyberwave (i.e. a Dockerized service that reads hardware state and publishes it as twin metadata), suggest they use the `/cyberwave-driver` skill instead — it is purpose-built for that.

**Additional install — camera support:**

```bash
pip install cyberwave[camera]      # Standard cameras via OpenCV
pip install cyberwave[realsense]   # Intel RealSense (RGB + Depth)
```

FFMPEG is also required for video streaming (`brew install ffmpeg` / `apt install ffmpeg`).

#### AE1 — Connect to a twin

Same as AR1 — the application authenticates with the same API key and connects to the twin it runs alongside.

```python
robot = cw.twin("the-robot-studio/so101")
```

#### AE2 — Stream video from the local camera (WebRTC)

The application opens the physical camera on the device and streams it to the Cyberwave platform via WebRTC.

**Simple case — `start_streaming()` (recommended):**

```python
from cyberwave import Cyberwave

cw    = Cyberwave()
robot = cw.twin("the-robot-studio/so101")

robot.start_streaming()  # blocks until Ctrl+C, then cleans up automatically
```

Pass `fps` and `camera_id` to override defaults:

```python
robot.start_streaming(fps=15, camera_id=1)
```

**Advanced case — `stream_video_background()` (async, non-blocking):**

Use this when you need to run other code alongside the stream, such as a local inference loop:

```python
import asyncio
from cyberwave import Cyberwave

async def run():
    cw    = Cyberwave()
    robot = cw.twin("the-robot-studio/so101")

    await robot.stream_video_background(fps=30)
    try:
        while True:
            # run inference, process data, etc.
            await asyncio.sleep(0.033)
    finally:
        await robot.stop_streaming()
        cw.disconnect()

asyncio.run(run())
```

#### AE3 — Raise alerts based on local state

Alerts are created on the twin from on-device logic — for example, when a sensor reading goes out of bounds or a vision model detects an anomaly.

```python
alert = robot.alerts.create(
    name="Calibration needed",
    description="Joint 3 is out of tolerance",
    severity="warning",      # "info" | "warning" | "error" | "critical"
    alert_type="calibration_needed"
)

# Lifecycle
alert.acknowledge()
alert.resolve()
alert.silence()

# Query
open_alerts = robot.alerts.list(status="open")
```

#### AE4 — Offer to help build

Ask the user:

> "What would you like to implement first? I can help you set up the camera loop and inference pipeline, define alert thresholds, or structure the application so it restarts cleanly if the hardware disconnects."

---

## Path B — C++ SDK

Inform the user that the C++ SDK is **coming soon** and is not yet available for development:

> "The Cyberwave C++ SDK is currently in development and not yet publicly available.
>
> In the meantime, your options are:
>
> - **Python SDK** — full-featured today (see Path A above)
> - **APIs directly** — use the REST and MQTT APIs from any language, including C++ (see Path C below); you can use any standard MQTT client library (e.g. Eclipse Paho) and an HTTPS client (e.g. libcurl or cpp-httplib)
>
> Would you like to proceed with one of these alternatives?"

---

## Path C — APIs directly

Use the Cyberwave platform via its two raw APIs. This works in any language.

### C1 — Authentication

All REST requests require a Bearer token. Generate your API key from your profile page at [app.cyberwave.com](https://app.cyberwave.com) and include it in every request:

```
Authorization: Bearer YOUR_API_KEY
```

### C2 — REST API

The REST API is the right choice for **non-real-time operations**: creating and managing twins, retrieving historical data, configuring settings, managing users and permissions, triggering workflows, and querying assets.

**Base URL:** `https://api.cyberwave.com`

**Common resource groups:**

| Resource        | Purpose                                    |
| --------------- | ------------------------------------------ |
| `/twins`        | Create, read, update, delete digital twins |
| `/assets`       | Browse and manage the asset catalog        |
| `/environments` | Manage virtual environments                |
| `/workflows`    | List and trigger automation workflows      |
| `/edges`        | Register and manage edge devices           |
| `/workspaces`   | Workspace and project management           |

**Example — list your twins:**

```bash
curl -X GET https://api.cyberwave.com/twins \
  -H "Authorization: Bearer $CYBERWAVE_API_KEY" \
  -H "Content-Type: application/json"
```

**Example — create a twin:**

```bash
curl -X POST https://api.cyberwave.com/twins \
  -H "Authorization: Bearer $CYBERWAVE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "registry_id": "the-robot-studio/so101",
    "name": "my-robot",
    "environment_id": "env-uuid"
  }'
```

Direct the user to the full API reference at [docs.cyberwave.com/api-reference/overview](https://docs.cyberwave.com/api-reference/overview) for the complete schema of each resource.

### C3 — MQTT API

The MQTT API is the right choice for **real-time operations**: live joint commands, telemetry streaming, position/rotation updates, and WebRTC signalling.

**Broker:** `mqtt://mosquitto:1883` (use TLS in production)

**Topic patterns:**

| Direction | Topic                                     | Purpose                       |
| --------- | ----------------------------------------- | ----------------------------- |
| Subscribe | `cyberwave.joint.{asset_uuid}.update`     | Receive joint state updates   |
| Subscribe | `cyberwave.twin.{twin_uuid}.position`     | Receive 3D position updates   |
| Subscribe | `cyberwave.twin.{twin_uuid}.rotation`     | Receive rotation (quaternion) |
| Subscribe | `cyberwave.twin.{twin_uuid}.scale`        | Receive scale updates         |
| Subscribe | `cyberwave.twin.{twin_uuid}.webrtc-offer` | Receive WebRTC SDP offers     |
| Subscribe | `cyberwave.ping.{resource_uuid}.request`  | Health check pings            |
| Publish   | `cyberwave.pong.{resource_uuid}.response` | Health check responses        |

**Message format** — all payloads are JSON with a `timestamp` (Unix epoch):

```json
// Joint update
{
  "timestamp": 1712345678.123,
  "name": "shoulder_joint",
  "position": 0.785,      // radians or metres
  "velocity": 0.1,
  "effort": 0.0
}

// Position update
{
  "timestamp": 1712345678.123,
  "x": 1.0,
  "y": 0.0,
  "z": 0.5
}

// Rotation update (quaternion)
{
  "timestamp": 1712345678.123,
  "w": 1.0,
  "x": 0.0,
  "y": 0.0,
  "z": 0.0
}
```

**Python example using Paho MQTT:**

```python
import json, time
import paho.mqtt.client as mqtt

TWIN_UUID = "your-twin-uuid"
ASSET_UUID = "your-asset-uuid"

client = mqtt.Client()
client.username_pw_set(username="", password="YOUR_API_KEY")
client.connect("mosquitto", 1883)

# Publish a joint command
payload = {
    "timestamp": time.time(),
    "name": "shoulder_joint",
    "position": 0.785,
    "velocity": 0.0,
    "effort": 0.0,
}
client.publish(f"cyberwave.joint.{ASSET_UUID}.update", json.dumps(payload))

client.loop_forever()
```

Direct the user to the full MQTT reference at [docs.cyberwave.com/api-reference/mqtt/main](https://docs.cyberwave.com/api-reference/mqtt/main) for complete topic and schema documentation.

### C4 — Offer to help build

Ask the user:

> "What would you like to implement? I can help you write the REST client, set up the MQTT connection, structure the message loop, or handle authentication. What language are you using?"

---

## Notes for Claude

- **Always recommend the Python SDK first** unless the user has a specific reason to use the APIs directly or needs C++.
- **Ask remote vs on-device early** — the two Python sub-paths use different SDK features and mixing them up creates confusion. Clarify this before writing any code.
- **Driver vs on-device application** — if the user wants to bridge new hardware to Cyberwave (read hardware state → publish as twin metadata), that is a driver, not an application. Redirect them to `/cyberwave-driver`.
- **`source_type="sim"` is safe for development** — recommend it while the user is getting started so they don't accidentally send commands to real hardware.
- **FFMPEG and camera extras are on-device only** — only needed for `start_streaming()` / `stream_video_background()`. Remote applications that use `capture_frame()` do not need them.
- **`start_streaming()` first, `stream_video_background()` second** — `start_streaming()` is the 2-line blocking version (handles Ctrl+C automatically). Only reach for `stream_video_background()` when the user needs to run async code alongside the stream.
- **API key scoping** — `CYBERWAVE_API_KEY` is the primary credential; `CYBERWAVE_ENVIRONMENT_ID` is optional but useful to avoid passing it on every call.
- **Real-time vs REST** — when the user wants to command a robot in a loop, they should use MQTT (or the SDK which wraps it). REST is only for setup and configuration.
- **The platform is in Private Beta** — if the user doesn't have access yet, direct them to request early access at [cyberwave.com](https://cyberwave.com).
