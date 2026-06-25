# rover_nav_ws

Mars Rover simulation with Cartographer SLAM + Nav2 autonomous navigation in Ignition Gazebo Fortress / ROS 2 Humble.

## Package: `rover_nav`

### Structure
```
rover_nav_ws/
└── src/rover_nav/
    ├── config/
    │   ├── rover_cartographer.lua   # Cartographer 2D SLAM config
    │   └── nav2_params.yaml         # Nav2 params tuned for rover
    ├── launch/
    │   ├── mapping.launch.py        # Phase 1: build map with Cartographer
    │   └── navigation.launch.py     # Phase 2: autonomous Nav2 navigation
    ├── maps/                        # Save your map here
    ├── models/mars_rover/           # Rover SDF model
    └── worlds/rover_world.sdf       # Custom world with walls + boulders
```

---

## Install dependencies

```bash
sudo apt install -y \
  ros-humble-cartographer-ros \
  ros-humble-nav2-bringup \
  ros-humble-navigation2 \
  ros-humble-teleop-twist-keyboard \
  ros-humble-ros-gz-bridge \
  ros-humble-ros-gz-sim
```

---

## Build

```bash
cd ~/rover_nav_ws
colcon build --packages-select rover_nav
source install/setup.bash
```

---

## Workflow

### Phase 1 — Map the world with Cartographer

```bash
ros2 launch rover_nav mapping.launch.py
```

In a second terminal, teleoperate the rover to build the map:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/cmd_vel
```

In RViz:
- Add Map display → topic `/map`
- Add LaserScan → topic `/lidar`
- Set Fixed Frame to `map`

Drive around all the obstacles until the map is fully built.

### Save the map

```bash
mkdir -p ~/rover_nav_ws/src/rover_nav/maps
ros2 run nav2_map_server map_saver_cli \
  -f ~/rover_nav_ws/src/rover_nav/maps/rover_map
```

Rebuild after saving:
```bash
cd ~/rover_nav_ws
colcon build --packages-select rover_nav
source install/setup.bash
```

---

### Phase 2 — Autonomous navigation with Nav2

```bash
ros2 launch rover_nav navigation.launch.py
```

In RViz:
1. Add Map → `/map`
2. Add Map → `/global_costmap/costmap`
3. Add Map → `/local_costmap/costmap`
4. Set Fixed Frame to `map`
5. Click **2D Pose Estimate** → click where rover is on the map
6. Wait for AMCL to localize (particle cloud converges)
7. Click **2D Goal Pose** → click destination → rover navigates autonomously

---

## Key topics

| Topic | Type | Notes |
|-------|------|-------|
| `/cmd_vel` | Twist | Drive commands |
| `/odom` | Odometry | Wheel odometry |
| `/lidar` | LaserScan | 360° 2D LiDAR |
| `/map` | OccupancyGrid | Cartographer map |
| `/global_costmap/costmap` | OccupancyGrid | Nav2 global plan |
| `/local_costmap/costmap` | OccupancyGrid | Nav2 local avoidance |

---

## Notes

- Rover base frame in Ignition: `mars_rover/chassis`
- LiDAR frame: `mars_rover/lidar_link`
- If AMCL drifts, re-click **2D Pose Estimate** to reset localization
- Robot radius set to 0.7m in nav2_params — adjust if rover collides with walls
