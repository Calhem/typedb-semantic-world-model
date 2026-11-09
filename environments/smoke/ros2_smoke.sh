#!/usr/bin/env bash
# ROS 2 Lyrical + Gazebo + Nav2 smoke test (Phase 1C). Headless; nothing persists outside the container.
#   docker run --rm -v "$PWD:/work" wm-ros2:lyrical bash /work/environments/smoke/ros2_smoke.sh
# Checks: simulator clock and sensors, TF tree, Nav2 action server, one navigation goal, an MCAP recording.
# (no "set -u": ROS setup scripts read unset variables)
. /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=57 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
LOG=/tmp/sim.log
step() { echo; echo "== $*"; }

step "versions"
echo "ROS_DISTRO=$ROS_DISTRO"; gz sim --versions | head -1; python3 --version; grep PRETTY /etc/os-release

step "launch Gazebo (headless) + TurtleBot3 + Nav2 (AMCL on the sandbox map)"
ros2 launch nav2_bringup tb3_simulation_launch.py headless:=True use_rviz:=False > $LOG 2>&1 &
LAUNCH=$!
for i in $(seq 1 90); do ros2 action list 2>/dev/null | grep -q /navigate_to_pose && break; sleep 2; done
ros2 action list | grep -E "navigate_to_pose" || { echo "FAIL: no navigate_to_pose after 180 s"; tail -40 $LOG; kill $LAUNCH; exit 1; }

step "topics present"
ros2 topic list | grep -E "^/(clock|scan|odom|tf|tf_static|amcl_pose|map)$"

step "sensor and clock rates (sim time)"
timeout 12 ros2 topic hz /scan --window 20 2>/dev/null | tail -2
timeout 12 ros2 topic hz /odom --window 20 2>/dev/null | tail -2

step "one Detection3D-compatible message type is available"
ros2 interface show vision_msgs/msg/Detection3D | grep -E "^(std_msgs|ObjectHypothesisWithPose|BoundingBox3D|string)"

step "set initial pose, wait for map -> base_link"
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {frame_id: map}, pose: {pose: {position: {x: -2.0, y: -0.5}, orientation: {w: 1.0}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.068]}}" >/dev/null
for i in $(seq 1 30); do timeout 5 ros2 run tf2_ros tf2_echo map base_link 2>/dev/null | grep -q Translation && break; sleep 2; done
timeout 6 ros2 run tf2_ros tf2_echo map base_link 2>/dev/null | grep -m1 -A1 "At time"

step "record 15 s of /scan /odom /tf /clock /amcl_pose (MCAP)"
ros2 bag record -o /tmp/smoke_bag --topics /scan /odom /tf /clock /amcl_pose > /tmp/bag.log 2>&1 &
BAG=$!

step "send a NavigateToPose goal (1.5 m ahead), up to 150 s"
timeout 150 ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: -0.5, y: -0.5}, orientation: {w: 1.0}}}}" 2>&1 \
  | grep -E "Goal accepted|Goal finished|status|error_code" | head -6
sleep 2
# Background jobs in a non-interactive shell ignore SIGINT, so stop the recorder with SIGTERM (rosbag2 closes the file cleanly).
kill -TERM $BAG 2>/dev/null; timeout 20 tail --pid=$BAG -f /dev/null
echo "recorder log:"; tail -5 /tmp/bag.log

step "bag info"
ros2 bag info /tmp/smoke_bag | grep -E "Storage id|Duration|Messages|Topic:" | head -10

step "shutdown"
kill -TERM $LAUNCH 2>/dev/null; sleep 5; pkill -f "gz sim" 2>/dev/null
echo "[ERROR] lines in launch log: $(grep -c '\[ERROR\]' $LOG)"; grep '\[ERROR\]' $LOG | sed -E 's/\[[0-9.]+\]//' | cut -c1-200 | sort | uniq -c | sort -rn | head -8
echo "tf start-up messages (before AMCL publishes map): $(grep -c 'Timed out waiting for transform' $LOG)"
echo "SMOKE DONE"
