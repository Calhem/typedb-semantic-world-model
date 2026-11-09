# ROS 2 Lyrical + Gazebo (via ros_gz) + Nav2 + TurtleBot3 minimal simulation, headless (Phase 1C).
# Base pinned by digest. apt packages are pinned to the versions verified on 2026-11-09; the ROS apt repository keeps only
# current versions, so a later rebuild may need these pins updated (environments/ros2/packages.lock records what was built).
FROM ros:lyrical-ros-base-resolute@sha256:3224ee150cb02eb89a5e0811bc267b57ed3a91b9c10191df57810726a7e916d7

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-lyrical-navigation2=1.5.2-2resolute.20260921.023050 \
      ros-lyrical-nav2-bringup=1.5.2-2resolute.20260930.004326 \
      ros-lyrical-nav2-minimal-tb3-sim=1.3.0-1resolute.20260930.003000 \
      ros-lyrical-ros-gz=3.0.10-1resolute.20260930.003553 \
      ros-lyrical-vision-msgs=4.2.0-3resolute.20260915.044604 \
      ros-lyrical-rosbag2-storage-mcap=0.33.4-1resolute.20260919.190531 \
      mesa-utils libegl1 libgl1-mesa-dri \
    && rm -rf /var/lib/apt/lists/* \
    && dpkg-query -W -f='${Package}=${Version}\n' | sort > /opt/packages.lock

# Software rendering for sensors in a container without a GPU.
ENV LIBGL_ALWAYS_SOFTWARE=1 \
    QT_QPA_PLATFORM=offscreen \
    ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
WORKDIR /work
