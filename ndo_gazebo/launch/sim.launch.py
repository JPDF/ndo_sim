import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
)
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
    AnyLaunchDescriptionSource,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition, UnlessCondition
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit


def generate_launch_description():
    pkg_name = "ndo_gazebo"
    pkg_share = FindPackageShare(pkg_name).find(pkg_name)
    params_file = os.path.join(pkg_share, "config", "gazebo_params.yaml")
    model = os.path.join(pkg_share, "urdf", "ndo.gazebo.xacro")

    desc_pkg_name = "ndo_description"
    desc_pkg_share = FindPackageShare(desc_pkg_name).find(desc_pkg_name)
    rsp_launch = os.path.join(desc_pkg_share, "launch", "rsp.launch.py")
    rviz_config_path = os.path.join(desc_pkg_share, "rviz", "urdf_config.rviz")

    gazebo_pkg_name = "gazebo_ros"
    gazebo_pkg_share = FindPackageShare(gazebo_pkg_name).find(gazebo_pkg_name)
    gazebo_launch = os.path.join(gazebo_pkg_share, "launch", "gazebo.launch.py")

    ctrl_pkg_name = "ndo_controller"
    ctrl_pkg_share = FindPackageShare(ctrl_pkg_name).find(ctrl_pkg_name)
    ctrl_launch = os.path.join(ctrl_pkg_share, "launch", "load.launch.py")

    teleop_pkg_name = "ndo_teleop"
    teleop_pkg_share = FindPackageShare(teleop_pkg_name).find(teleop_pkg_name)
    teleop_launch = os.path.join(teleop_pkg_share, "launch", "teleop.launch.xml")

    enable_teleop = LaunchConfiguration("teleop")
    enable_rviz = LaunchConfiguration("rviz")

    teleop = IncludeLaunchDescription(
        AnyLaunchDescriptionSource([teleop_launch]),
        launch_arguments={"out": "/diff_ctrl/cmd_vel_unstamped"}.items(),
        condition=IfCondition(enable_teleop),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
        condition=IfCondition(enable_rviz)
    )
    
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([rsp_launch]),
        launch_arguments={"use_sim_time": "true", "model": model}.items()
    )

    # Include the Gazebo launch file, provided by the gazebo_ros package
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gazebo_launch]),
        launch_arguments={
            "extra_gazebo_args": "--ros-args --params-file " + params_file
        }.items(),
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "ndo"],
        output="screen",
    )

    controllers = IncludeLaunchDescription(PythonLaunchDescriptionSource([ctrl_launch]))

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                name="teleop",
                default_value="true",
                description="Flag to enable teleop",
            ),
            DeclareLaunchArgument(
                name="rviz",
                default_value="true",
                description="Flag to enable rviz",
            ),
            rsp,
            gazebo,
            spawn_entity,
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=spawn_entity,
                    on_exit=[controllers, teleop, rviz],
                )
            )
        ]
    )
