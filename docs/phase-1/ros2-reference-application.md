# Reference application C: ROS 2 robotics integration

**Status: research and design only.** Nothing is installed or downloaded; no adapter code exists yet. Facts about
ROS 2 below are from published documentation to mid-2026 and should be checked against the chosen distribution's
docs when Phase R starts.

ROS 2 (Robot Operating System 2) is the standard open-source middleware for robots: programs called **nodes**
exchange typed **messages** on named **topics** (streams), call **services** (request/response) and run **actions**
(long tasks with feedback, like "navigate to the dock").

## The boundary: what stays in ROS 2, what reaches TypeDB
| Stays in ROS 2 (fast, real-time or high-rate) | Reaches TypeDB (slow, persistent, semantic) |
|---|---|
| Raw sensors: images, point clouds, IMU, lidar scans (10-1000 Hz) | Observations *summarised*: "object detected", with a reference to the bag message |
| TF2 transforms at full rate | Poses of tracked objects in `map` frame, when they change by more than a threshold, plus the frame chain used |
| Localisation, SLAM, costmaps | Map versions and named places (rooms, shelves, docks), not occupancy cells |
| Nav2 planning and control, actuation | Navigation goals and outcomes as events (goal accepted, succeeded, aborted, why) |
| Object tracking (track ids) | Identity claims: track → referent, with evidence |

**Hard rule:** no control loop ever waits on TypeDB. The adapter is an ordinary, low-priority node. If TypeDB is
slow or down, the robot behaves exactly as it would without the adapter.

## Mapping ROS 2 concepts to the core
| ROS 2 | Core concept |
|---|---|
| `std_msgs/Header.stamp` | observation time (sim time when `use_sim_time` is set: record which clock) |
| `header.frame_id`, TF2 tree (REP 105: `map`, `odom`, `base_link`) | frame reference on spatial claims; transforms are resolved in ROS before writing |
| `vision_msgs/Detection3DArray` (class hypotheses with scores) | observation + `classified-as` claims with confidence (one per hypothesis, not just the top one) |
| covariance matrices (pose, odometry) | `measurement` uncertainty (diagonal in v1) |
| tracker id | sensor-local id → `refers-to` claim to a referent |
| Nav2 action goals, behaviour-tree events | `event` subtypes with participants (robot, goal place) |
| node name, topic, bag file, message index | observation source and raw reference (PROV) |
| a world in Gazebo vs the real site | `world` (simulated vs actual) |

## Adapter design (to build in Phase R, after review)
- A Python (`rclpy`) node, `world_model_adapter`, with:
  1. **Subscribers** for a configured, small set of topics; a **reducer** per topic that turns a stream into
     semantic events (appear, move > d metres, disappear after t seconds, class change, goal outcome).
  2. **Identity resolver**: keeps track → referent links; ambiguous links become claims to review, not merges.
  3. **Writer**: batches claims into TypeDB write transactions on a separate thread, with deterministic ids
     derived from (source, topic, stamp, sequence), so replaying a bag twice writes nothing new.
  4. **Outage spool**: when TypeDB is unreachable, batches go to a bounded on-disk spool and are replayed in order.
     Older batches are dropped *and counted* when the spool is full. (Open decision: whether this file conflicts with
     the "TypeDB only" rule; it is a buffer, not a queried store.)
  5. **Query service**: a ROS 2 service exposing **named queries only** (where-is, last-seen, what-happened-in,
     who-did), as the explorer does, plus a low-rate topic publishing a world summary.
- **Deterministic replay** with rosbag2 (MCAP format) and `--clock`, so every run of an experiment is identical.

## Environment (decisions needed)
- **ROS 2 is not well supported on macOS.** Run it in Docker (official `ros:<distro>` images exist for arm64) or on a
  Linux machine. Simulation GUIs in Docker on a Mac are awkward: run Gazebo headless, or replay recorded bags.
- **Distribution:** Jazzy Jalisco (LTS, 2024) or the 2026 LTS release. Recommend whichever LTS has Nav2 binaries for
  arm64 when we start.
- **Data:** generate our own bags from a simulated warehouse (Gazebo + Nav2 sample worlds), with ground truth from
  the simulator, which gives *independent* annotation for free: the simulator knows where everything really is.
  This is the strongest evaluation advantage of the robotics track.
- Pulling images and simulation assets is a download: **needs owner approval** first.

## Evaluation (Experiment R)
**B0 (ROS-native baseline):** the same reducers feeding an in-memory dictionary of current state plus an append-only
JSON event log, exposed through the same ROS service. Optionally a second baseline: an existing scene-graph package.

| Metric | How |
|---|---|
| Semantic mapping correctness | adapter claims vs simulator ground truth (object places, events) |
| Identity continuity | fraction of ground-truth objects with one referent over the run; wrongful merges and splits |
| Temporal consistency | CQs 1, 2, 5, 6 at sampled times vs ground truth; unsupported assertions |
| Query latency | p50 / p95 of each named query from a ROS client, both stores |
| Ingestion throughput | semantic events / s sustained; max bag replay speed without backlog |
| Memory and CPU | adapter node and TypeDB server RSS and CPU (docker stats, `/proc`), vs B0 |
| Data reduction | bytes in the bag's raw topics vs bytes of semantic records written |
| Network interruption / DB down | kill and restart TypeDB mid-replay: robot topics unaffected (message rates), spool size, records lost, time to catch up |
| Interoperability | export to `wop-memory-1` and `wop-visual-1`; CQ 21 |

**Success (brief):** a ROS 2 application builds, updates and queries a persistent semantic representation with the
shared core, with latency and resource overhead we state in advance. Proposed thresholds, for review: no effect on
control-topic rates; named queries p95 < 50 ms on the robot computer; adapter + server < 1 GB RAM for a one-hour
warehouse run. **Where B0 is as good, we say so.** The expected TypeDB win is in historical, provenance and
cross-application questions (CQs 6, 13, 19, 20, 21), not in "where is it now".
