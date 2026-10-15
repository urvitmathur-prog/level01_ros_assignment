#!/usr/bin/env python3
"""Run AMCL localization against the map published by map_loader.launch.py."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    nav_dir = get_package_share_directory('testbed_navigation')

    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')

    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(nav_dir, 'config', 'amcl_params.yaml'),
        description='Full path to the AMCL parameter file')

    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use the Gazebo /clock if true')

    declare_autostart = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Automatically configure and activate AMCL')

    # AMCL: particle-filter localization. Subscribes to /map, /scan and TF (odom -> base),
    # publishes map -> odom, /amcl_pose and /particle_cloud
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}])

    # Separate lifecycle manager so localization can be started/stopped
    # independently of map loading and navigation
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time,
                     'autostart': autostart,
                     'bond_timeout': 10.0,   # slow VM: avoid false 'server down' shutdowns
                     'node_names': ['amcl']}])

    return LaunchDescription([
        declare_params,
        declare_sim_time,
        declare_autostart,
        amcl,
        lifecycle_manager,
    ])
