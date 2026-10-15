#!/usr/bin/env python3
"""Send a NavigateToPose goal to Nav2 by calling the action directly.

Usage:
  ros2 run testbed_navigation send_goal.py <x> <y> [yaw_rad]
  e.g. ros2 run testbed_navigation send_goal.py 2.0 5.0 1.57
"""
import math
import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose


class GoalSender(Node):
    def __init__(self):
        super().__init__('send_goal')
        self.client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

    def send(self, x, y, yaw):
        if not self.client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('navigate_to_pose action server not available '
                                    '(is navigation.launch.py running?)')
            return False

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        # header.stamp left at 0 = "use the latest transform" (avoids wall/sim clock mismatch)
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.get_logger().info(f'Sending goal: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f} rad')
        send_future = self.client.send_goal_async(goal, feedback_callback=self.on_feedback)
        rclpy.spin_until_future_complete(self, send_future)
        handle = send_future.result()
        if not handle.accepted:
            self.get_logger().error('Goal rejected')
            return False

        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        status = result_future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Goal reached!')
            return True
        self.get_logger().warn(f'Goal did not succeed (status code {status})')
        return False

    def on_feedback(self, msg):
        self.get_logger().info(
            f'Distance remaining: {msg.feedback.distance_remaining:.2f} m',
            throttle_duration_sec=2.0)


def main():
    rclpy.init()
    args = rclpy.utilities.remove_ros_args(sys.argv)[1:]
    if len(args) < 2:
        print(__doc__)
        rclpy.shutdown()
        sys.exit(1)
    x, y = float(args[0]), float(args[1])
    yaw = float(args[2]) if len(args) > 2 else 0.0

    node = GoalSender()
    ok = node.send(x, y, yaw)
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
