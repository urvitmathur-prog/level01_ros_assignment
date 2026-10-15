#!/usr/bin/env python3
"""Bring up the Nav2 navigation servers individually (no nav2_bringup).

Requires map_loader.launch.py and localization.launch.py to be running.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    nav_dir = get_package_share_directory('testbed_navigation')
    bt_dir = get_package_share_directory('nav2_bt_navigator')

    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    bt_xml = LaunchConfiguration('bt_xml')

    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(nav_dir, 'config', 'nav2_params.yaml'),
        description='Full path to the Nav2 parameter file')

    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use the Gazebo /clock if true')

    declare_autostart = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Automatically configure and activate the navigation servers')

    declare_bt_xml = DeclareLaunchArgument(
        'bt_xml',
        default_value=os.path.join(
            bt_dir, 'behavior_trees', 'navigate_to_pose_w_replanning_and_recovery.xml'),
        description='Behavior tree used for NavigateToPose')

    common = [params_file, {'use_sim_time': use_sim_time}]

    # Global planner: computes a path on the global costmap (map frame)
    planner_server = Node(
        package='nav2_planner', executable='planner_server',
        name='planner_server', output='screen',
        parameters=common)

    # Local controller: follows the path using the local costmap (odom frame).
    # Output goes to the velocity smoother, not directly to the robot.
    controller_server = Node(
        package='nav2_controller', executable='controller_server',
        name='controller_server', output='screen',
        parameters=common,
        remappings=[('cmd_vel', 'cmd_vel_nav')])

    # Recovery behaviors used by the behavior tree: spin, backup, wait
    behavior_server = Node(
        package='nav2_behaviors', executable='behavior_server',
        name='behavior_server', output='screen',
        parameters=common)

    # Behavior tree navigator: exposes the /navigate_to_pose action
    bt_navigator = Node(
        package='nav2_bt_navigator', executable='bt_navigator',
        name='bt_navigator', output='screen',
        parameters=[params_file,
                    {'use_sim_time': use_sim_time,
                     'default_nav_to_pose_bt_xml': bt_xml}])

    # Smooths controller output: cmd_vel_nav -> cmd_vel (to Gazebo diff-drive)
    velocity_smoother = Node(
        package='nav2_velocity_smoother', executable='velocity_smoother',
        name='velocity_smoother', output='screen',
        parameters=common,
        remappings=[('cmd_vel', 'cmd_vel_nav'),
                    ('cmd_vel_smoothed', 'cmd_vel')])

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation', output='screen',
        parameters=[{'use_sim_time': use_sim_time,
                     'autostart': autostart,
                     'bond_timeout': 10.0,   # slow sim: avoid false "node died" resets
                     'node_names': ['controller_server',
                                    'planner_server',
                                    'behavior_server',
                                    'bt_navigator',
                                    'velocity_smoother']}])

    return LaunchDescription([
        declare_params,
        declare_sim_time,
        declare_autostart,
        declare_bt_xml,
        controller_server,
        planner_server,
        behavior_server,
        bt_navigator,
        velocity_smoother,
        lifecycle_manager,
    ])
