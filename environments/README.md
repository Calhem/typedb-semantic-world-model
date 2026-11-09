# Experimental environments (Phase 1C)

Verified on 2026-11-09 on the project machine: Apple Silicon (arm64) Mac, Docker Desktop (server 29.9.2, 10 CPUs,
7.7 GiB memory to the VM). Isolated from the other projects: compose project `wm-env`, containers `wm-*`, named
volumes `wm-*`, ports bound to 127.0.0.1 only (5435, 1735, 8006). No ontology, adapter or application code is here.

## Pre-installation checks
| Check | Result |
|---|---|
| Host disk free before installing | 194 GiB (of 460 GiB) |
| Docker usage before | 2.3 GB images, 4.3 GB build cache |
| Docker VM disk | sparse 460 GB file, 9 GB used; effective limit is host free space |
| Platform | arm64; PostgreSQL 18.6 and ROS 2 Lyrical publish arm64 images; ROS Lyrical on Ubuntu 26.04 arm64 is Tier 1 (macOS is Tier 3, so ROS runs in Docker) |
| Ports | 1729-1734, 8002-8005, 8090-8092, 5180 used by other projects; 5435, 1735, 8006 free |
| Host disk free after installing | 176 GiB |

## Pinned versions
| Component | Version | Pin |
|---|---|---|
| PostgreSQL | 18.6 (Debian 18.6-1.pgdg13+2), aarch64 | `postgres:18.6-trixie@sha256:e3d24f6906d0760bf4da0dae872415391ededefad23fd471c47dc53b0ddf3c42` (666 MB) |
| TypeDB (isolated) | TypeDB CE 3.14.1 | `typedb/typedb:3.14.1@sha256:d39d4f29eb571ee856cb221e8175b76dcb96dfa39939ebde5360cffa0e5bb680` (already on the machine; no download) |
| ROS 2 base | Lyrical Luth on Ubuntu 26.04.1 LTS, Python 3.14.4 | `ros:lyrical-ros-base-resolute@sha256:3224ee150cb02eb89a5e0811bc267b57ed3a91b9c10191df57810726a7e916d7` |
| Gazebo | Gazebo Sim 10.5.0 (Jetty), via `ros-lyrical-ros-gz` 3.0.10 | apt pins in `ros2/Dockerfile` |
| Nav2 | `ros-lyrical-navigation2` 1.5.2, `nav2-bringup` 1.5.2, `nav2-minimal-tb3-sim` 1.3.0 | apt pins |
| Others | `vision-msgs` 4.2.0, `rosbag2` + `rosbag2-storage-mcap` 0.33.4, `tf2-ros` 0.45.10, `rclpy` 10.0.11 | apt pins; full list `ros2/packages.lock` (1,740 packages) |
| Built image | `wm-ros2:lyrical`, **7.4 GB** uncompressed | local only |

**Reproducibility limit:** the ROS apt repository keeps only current package versions. The Dockerfile pins the
versions above, so a rebuild fails loudly rather than silently drifting once they are replaced. To rebuild exactly
later, keep the built image (`docker save wm-ros2:lyrical`) or update the pins and record the new lock file.
Phase 1B estimated 2-3 GB for this image; it is 7.4 GB, mostly Gazebo and its dependencies.

## Steps
```bash
docker compose -f environments/compose.yaml up -d postgres typedb
docker exec -i wm-postgres psql -U wm -d wm -v ON_ERROR_STOP=0 < environments/smoke/postgres_smoke.sql
docker compose -f environments/compose.yaml --profile ros2 build ros2
docker run --rm -v "$PWD:/work:ro" wm-ros2:lyrical bash /work/environments/smoke/ros2_smoke.sh
```

## Smoke test results
**PostgreSQL** (`smoke/postgres_smoke.out`):
- version 18.6; `btree_gist` loads
- temporal primary key `WITHOUT OVERLAPS` **rejects** an overlapping valid time for the same object
- temporal foreign key `PERIOD` **rejects** a reference outside the referent's lifetime
- as-of query returns the right row. **Caveat:** an open-ended range `[10:12,)` answered "dock" at 10:15,
  i.e. PostgreSQL ranges read a missing end as "still true". Baseline B must encode unknown ends explicitly to meet
  the specification (Phase 1C semantic review §2.3)
- throwaway schema dropped; 0 left

**Isolated TypeDB:** server reports TypeDB CE 3.14.1; a test database was created, defined, queried and deleted; 0
databases left.

**ROS 2 + Gazebo + Nav2** (`smoke/ros2_smoke.out`, 57 s wall time):
- headless Gazebo with TurtleBot3 (waffle) on the sandbox world, Nav2 with AMCL, `use_sim_time`
- topics `/clock /scan /odom /tf /tf_static /amcl_pose /map` present; `/scan` 5.0 Hz, `/odom` 27.1 Hz (sim time)
- `map → base_link` resolves after the initial pose
- `vision_msgs/msg/Detection3D` available (header, results, bbox, id)
- one `NavigateToPose` goal: **SUCCEEDED**, error code 0
- MCAP recording: 6.1 s, 2,517 messages over 5 topics; the recorder reported **3 messages lost on the transport
  layer** (to watch when measuring data reduction)
- 0 `[ERROR]` lines; 55 informational "waiting for transform" messages before AMCL publishes `map` (normal start-up)

**Pitfalls found** (for whoever builds the adapter): `ros2 bag record` in Lyrical needs `--topics`; ROS setup
scripts fail under `set -u`; background processes in non-interactive shells ignore SIGINT, so stop recorders with
SIGTERM.
