# 5. Updated ROS 2 and GUPI assessments

Labels: **V** verified this phase (source named), **I** interpretation, **A** assumption.

## 5.1 ROS 2: verified facts
| Topic | Fact | Source | |
|---|---|---|---|
| Distribution | **Lyrical Luth**, May 2026, LTS, supported until **May 2031** | ros2_documentation `Releases/Release-Lyrical-Luth.rst` | V |
| Platforms | Ubuntu 26.04 amd64 and **arm64: Tier 1**; **macOS: Tier 3** (build from source) | `lyrical/supported-platforms.rst` | V |
| Simulator pairing | **Gazebo Jetty** with Lyrical | same file | V |
| Container images | `ros:lyrical-ros-base` for arm64, about 341 MB compressed; `lyrical-perception` about 1.5 GB | Docker Hub tag API (nothing pulled) | V |
| Binary packages (arm64) | `navigation2`, `nav2-bringup`, `nav2-minimal-tb3-sim`, `turtlebot3-gazebo`, `ros-gz`, `rosbag2`, `tf2-ros`, `vision-msgs` all exist for Lyrical on Ubuntu 26.04 arm64 | packages.ros.org index | V |
| Frames (REP 105) | `map` is world-fixed but **not continuous: poses can jump** when localisation corrects; `odom` is continuous but drifts | REP 105 source | V |
| tf2 buffer | default cache **10 seconds** (`BUFFER_CORE_DEFAULT_CACHE_TIME`) | geometry2 `buffer_core.hpp` | V |
| Recording | rosbag2 default storage is **MCAP** | rosbag2 README | V |
| Detections | `Detection3D`: header, `results[]` of `ObjectHypothesisWithPose` (class hypothesis + score + `PoseWithCovariance`), `bbox`, and `id`, "used for consistency across multiple detection messages... may be empty" | vision_msgs `.msg` files | V |
| Navigation | `NavigateToPose` action: goal pose and behaviour tree; result with error codes (`GOAL_REJECTED`, `TF_ERROR`, `TIMEOUT`...); feedback with recoveries, distance remaining | nav2_msgs `.action` | V |
| Scene graphs on ROS 2 | Hydra (Jazzy, default since 07/2025); Khronos ROS 2 (10/2025, "unstable") | repositories | V |
| Licences | geometry2 BSD-3; rosbag2 and vision_msgs Apache-2.0; navigation2 mixed (GitHub: NOASSERTION) | GitHub API | V |

## 5.2 What the verified facts change
1. **Map-frame poses are revisable.** Because `map` jumps on relocalisation (V), a pose recorded in `map` at 10:03
   may later be corrected. Spatial claims must store the frame **and** the localisation estimate they used. A
   correction becomes a supersession with transaction time. Phase 1 treated poses as plain observations.
2. **Transform within the tf2 window.** With a 10 s default buffer (V), the adapter must resolve transforms when
   messages arrive (or keep its own buffer). It cannot look them up later from the database. During bag replay,
   `/clock` must drive time (`use_sim_time`), and the `sim` time reference system is recorded.
3. **Tracker ids are not identities.** `Detection3D.id` is optional and only consistent within one detector (V).
   The identity resolver is required, not optional.
4. **Keep all class hypotheses.** `results[]` holds several scored hypotheses with their own poses (V). Each becomes
   a competing `classified-as` claim, so the ontology's uncertainty model (2.6) is exercised directly.
5. **Navigation outcomes are rich events.** Goal, outcome, error code and recovery count map onto an `event` with
   participants and result attributes.
6. **Consume scene graphs, don't rebuild them.** Hydra and Khronos run on ROS 2 (V). Our adapter should accept their
   objects, places and change events as observations. That keeps perception out of the semantic layer.

## 5.3 Boundary: ROS 2 vs the persistent semantic layer (revised)
| Stays in ROS 2 | Goes to the semantic layer |
|---|---|
| Sensor streams, TF at full rate, localisation, SLAM, costmaps, planning, control, actuation | Observations summarised to semantic events, with a reference to the bag message |
| Current pose lookup (tf2), reachability, path costs: computed on demand (KnowRob 2.0's "virtual" lesson, V) | History: where things were, when, on what evidence |
| Scene graph construction (Hydra/Khronos) | Persistent identities across sessions and robots; `refers-to` claims from tracks and scene-graph nodes |
| Short-term tracking | Beliefs of several agents; corrections; provenance |
| — | Named places and map versions, not occupancy cells |

**Runtime rules:** the adapter is its own process with a best-effort, keep-last QoS on inputs. Database writes run
on a worker thread, never in an executor callback. Query services have timeouts. No control node calls the
semantic layer synchronously. **Measured invariant:** topic rates and control latencies are the same with the
adapter running, stopped, and with TypeDB killed.

## 5.4 Simulator and environment options
| Option | Verdict |
|---|---|
| **Gazebo Jetty + `nav2_minimal_tb3_sim` (TurtleBot3)** in `ros:lyrical` on Docker, headless | **Recommended.** All packages verified for arm64; ground truth from the simulator. Size: ros-base 341 MB compressed plus Gazebo and Nav2 layers (estimate 1.5-3 GB; A). **Needs approval** |
| Warehouse world assets (e.g. a small-warehouse Gazebo world) | Licence and Jetty compatibility unchecked (A) |
| NVIDIA Isaac Sim | Rejected: needs an NVIDIA GPU, which this Mac lacks (I) |
| Webots | Possible alternative (A) |
| Public rosbags | Useful for throughput tests; no semantic ground truth |

**Plan (unchanged in substance):** ROS 2 is the first substantial integration experiment, after architectural
approval. A one-day environment trial (pull images, run the TB3 sim headless, record a bag) comes first, and stops
for review if Docker on this Mac is impractical.

## 5.5 GUPI: three different qualities
Phase 1 treated GUPI only as "parity". The brief is right that this is too narrow. The three qualities need
different measures:

| Quality | Question it answers | Measure | Status in GUPI (V, final report) |
|---|---|---|---|
| **Retrieval quality** | Did the right evidence reach the answerer? | Recall@k of gold evidence | Measured on LoCoMo / LongMemEval (development); claims gave no recall gain on chat |
| **Answer correctness** | Is the final answer right? | Accuracy against independent gold answers; unsupported-assertion rate | **Never measured independently** |
| **Semantic consistency** | Is the memory itself coherent? | Contradictions surfaced vs hidden; unsupported definitive answers; temporal violations; identity errors | Measured on developer-written fixtures only |

## 5.6 A controlled answer-quality baseline for GUPI (proposal)
**Data.** LongMemEval (MIT licence, V) has questions with gold answers written by its authors, so it is independent
of us. Use its temporal-reasoning, knowledge-update and multi-session categories (A: category names as remembered;
check before preregistration). LoCoMo's licence is unresolved (GUPI known issues, V) and is excluded unless you
decide otherwise.

**Conditions (same answering model, prompt template, token budget and retrieval budget):**
1. **Raw:** keyword + embedding retrieval over the conversation text.
2. **GUPI:** GUPI's claims with qualifications (dates, CONTESTED, UNKNOWN) plus the same raw retrieval.
3. **Profile:** the same through the world ontology's `wop-memory-1` profile (only after Phase 3 exists).
4. **Oracle-evidence control:** the gold evidence turns handed to the model, which bounds what retrieval can add.

**Scoring.** Exact or normalised match where possible; otherwise a judge model with a published rubric, plus a
human spot check of 20% (you, or someone independent). Unsupported-assertion rate reported separately.

**Budget constraint (V, memory of your decision):** no paid API calls. Within the Claude subscription, answering
runs as manual sessions, which limits the size to roughly 100-200 questions. That gives intervals around ±7-10
points. It is enough to detect a large effect, not a small one. The report must say so.

**Decision rule (proposal):** GUPI's structure is "useful for answers" only if condition 2 beats condition 1 by
≥ 5 points with an interval above zero, **without** a higher unsupported-assertion rate. Otherwise the result is
reported as no benefit.

**Strongest counterargument:** LongMemEval is chat-assistant memory, the domain where GUPI already found structure
does not help retrieval. A null result there says little about dense-relationship domains. Agreed. That is why
ROS 2 is the first integration, and the GUPI test is a secondary one.

## 5.7 What does not change
GUPI is not modified. Any adapter lives on a branch in the GUPI repository, after approval, and GUPI's results and
private data stay where they are.
