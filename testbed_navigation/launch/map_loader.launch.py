#!/usr/bin/env python3
"""Load the static map with nav2_map_server and bring it up via a lifecycle manager."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    nav_dir = get_package_share_directory('testbed_navigation')
    bringup_dir = get_package_share_directory('testbed_bringup')

    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(bringup_dir, 'maps', 'testbed_world.yaml'),
        description='Full path to the map YAML file')

    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(nav_dir, 'config', 'map_server_params.yaml'),
        description='Full path to the map_server parameter file')

    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use the Gazebo /clock if true')

    declare_autostart = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Automatically configure and activate the map_server')

    # The map server itself: a lifecycle node that reads the YAML and PGM files
    # and publishes a nav_msgs/OccupancyGrid on /map
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[params_file,
                    {'yaml_filename': map_yaml,
                     'use_sim_time': use_sim_time}])

    # Lifecycle nodes start "unconfigured" and do nothing until told to.
    # This manager moves map_server through configure -> activate.
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time,
                     'autostart': autostart,
                     'bond_timeout': 10.0,   # slow VM: avoid false 'server down' shutdowns
                     'node_names': ['map_server']}])

    return LaunchDescription([
        declare_map,
        declare_params,
        declare_sim_time,
        declare_autostart,
        map_server,
        lifecycle_manager,
    ])
