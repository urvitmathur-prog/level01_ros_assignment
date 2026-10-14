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
