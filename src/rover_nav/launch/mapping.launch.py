import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('rover_nav')
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_file = os.path.join(pkg, 'worlds', 'rover_world.sdf')

    gazebo = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', world_file],
        output='screen'
    )

    model_sdf = os.path.join(pkg, 'models', 'mars_rover', 'model.sdf')
    spawn_rover = ExecuteProcess(
        cmd=[
            'ign', 'service',
            '-s', '/world/rover_world/create',
            '--reqtype', 'ignition.msgs.EntityFactory',
            '--reptype', 'ignition.msgs.Boolean',
            '--timeout', '5000',
            '--req',
            f'sdf_filename: "{model_sdf}" '
            'name: "mars_rover" '
            'pose: {position: {x: 0.0, y: 0.0, z: 0.5}}'
        ],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/model/mars_rover/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/model/mars_rover/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/model/mars_rover/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/lidar@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        remappings=[
            ('/cmd_vel', '/model/mars_rover/cmd_vel'),
            ('/model/mars_rover/odometry', '/odom'),
            ('/model/mars_rover/tf', '/tf'),
        ],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    lidar_tf_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0',
                   'mars_rover/lidar_link',
                   'mars_rover/lidar_link/lidar_sensor'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    cartographer = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        arguments=[
            '-configuration_directory', os.path.join(pkg, 'config'),
            '-configuration_basename', 'rover_cartographer.lua'
        ],
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[
            ('/cmd_vel', '/model/mars_rover/cmd_vel'),('/scan', '/lidar')],
        output='screen'
    )

    cartographer_grid = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='cartographer_occupancy_grid_node',
        arguments=['-resolution', '0.05'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )
    chassis_to_lidar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0.5', '0', '0', '0',
                   'mars_rover/chassis',
                   'mars_rover/lidar_link'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        gazebo,
        TimerAction(period=3.0, actions=[spawn_rover]),
        TimerAction(period=5.0, actions=[
            bridge, lidar_tf_alias, chassis_to_lidar, cartographer, cartographer_grid, rviz
        ]),
    ])
