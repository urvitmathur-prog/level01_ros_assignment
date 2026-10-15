# Bugs Identified and Fixed

## 1. `testbed_description/CMakeLists.txt` — missing parentheses on `ament_package`
- **Symptom:** `colcon build` failed with `CMake Error ... Parse error. Expected "("`; `testbed_gazebo` also failed because it depends on `testbed_description`.
- **Cause:** The last line was `ament_package` instead of `ament_package()`. CMake commands always require parentheses.
- **Fix:** Changed it to `ament_package()`.

## 2. `testbed_bringup/CMakeLists.txt` — map folder not installed
- **Symptom:** `install/testbed_bringup/share/testbed_bringup/maps` did not exist, so the map could not be found by package path.
- **Cause:** `install(DIRECTORY ...)` only listed `launch`.
- **Fix:** Added `maps` to the install directories.

## 3. `testbed_gazebo/CMakeLists.txt` — models folder not installed
- **Symptom:** `spawn_playground.launch.py` adds `share/testbed_gazebo/models` to `GAZEBO_MODEL_PATH`, but that directory was never installed.
- **Cause:** `install(DIRECTORY ...)` only listed `launch` and `worlds`.
- **Fix:** Added `models` to the install directories.

## 4. `testbed_bringup/package.xml` — missing dependencies
- **Symptom:** The bringup launch file uses `testbed_gazebo`, `testbed_description`, `gazebo_ros` and `rviz2`, but none were declared.
- **Cause:** Incomplete `package.xml`, so build order and rosdep resolution weren't guaranteed.
- **Fix:** Added `<exec_depend>` entries for all four.

## 5. `testbed_description/launch/robot_description.launch.py` — robot_state_publisher not using sim time
- **Symptom:** `ros2 param get /robot_state_publisher use_sim_time` returned `False`, while RViz returned `True`.
- **Cause:** The node was launched without the `use_sim_time` parameter, so it used wall-clock time while Gazebo and the rest of the system used `/clock`.
- **Impact:** Mixed clocks produce TF timestamp mismatches ("extrapolation into the future/past") that break AMCL and the Nav2 costmaps. Today the impact is limited because the robot's transforms are mostly static, but it would fail as soon as anything published `/joint_states`.
- **Fix:** Added a `use_sim_time` launch argument (default `true`) and passed it to the node. Also wrapped `robot_description` in `ParameterValue(..., value_type=str)` so Humble doesn't try to parse the URDF as YAML.

## 6. `testbed_description/urdf/testbed.gazebo` — lidar max range far too short
- **Symptom:** `ros2 topic echo /scan --once` showed `range_max: 1.5`. The map is ~20 m × 20 m (405×400 px at 0.05 m/px), so most beams returned nothing.
- **Cause:** `<range><max>1.5</max>` in the ray sensor configuration.
- **Impact:** AMCL matches laser scans against the map walls; with a 1.5 m range it would rarely see any walls, making localization unreliable. Costmaps would also only see obstacles at very close range.
- **Fix:** Increased `<max>` to `12.0` m — realistic for an indoor 2D lidar and enough to see walls across the map. AMCL's `laser_max_range` was set to match.

## 7. `testbed_bringup/maps/testbed_world.yaml` — map image filename is wrong
- **Symptom:** `map_loader.launch.py` failed. `map_server` logged `Failed to load image file .../maps/wrong_path_testbed_world.pgm ... Unable to open file`, followed by `Callback returned ERROR during the transition: configure` and `lifecycle_manager_map: Failed to bring up all requested nodes. Aborting bringup.`
- **Cause:** The map YAML's `image:` field pointed to `wrong_path_testbed_world.pgm`, but the file in the `maps/` folder is `testbed_world.pgm`.
- **Impact:** `map_server` could not complete its *configure* lifecycle transition, so no map was published on `/map`. Without a map, AMCL cannot localize and the global costmap/planner cannot work — the whole navigation stack depends on this.
- **Fix:** Changed the line to `image: testbed_world.pgm`. The path is kept **relative**, so `map_server` resolves it from the YAML's own directory and it works on any machine, instead of hard-coding an absolute path like `/home/<user>/...`.
- **Verification:** `ros2 lifecycle get /map_server` → `active [3]`; `/map` reports a 405 × 400 grid at 0.05 m/cell; with a temporary identity `map → odom` transform, the live laser scan overlaid the map walls exactly, confirming the map frame is aligned with the Gazebo world frame.

## Other issues identified (not changed — no functional impact)
- `testbed.gazebo` loads `libgazebo_ros_control.so`, a ROS 1 plugin that does not exist in Humble. The robot is driven by `libgazebo_ros_diff_drive.so`, so it is unused.
- `testbed.gazebo` IMU plugin has a stray `>` after `<initial_orientation_as_reference>`.
- `Gazebo/Silver` is not a built-in Gazebo material, so the robot renders white (`Unable to get Material`).
- `.vscode/settings.json` contains a hard-coded path from the original developer's machine.

## Environment issues (not code bugs — see testbed_navigation/README.md)
- gzserver segfault on robot spawn with Cyclone DDS → resolved by using Fast DDS.
- Lifecycle bond timeouts on a CPU-starved VM → `bond_timeout: 10.0` on all lifecycle managers.
