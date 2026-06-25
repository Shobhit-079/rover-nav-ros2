import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('rover_nav')
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    map_file = os.path.join(pkg, 'maps', 'rover_map.yaml')
    world_file = os.path.join(pkg, 'worlds', 'rover_world.sdf')
    nav2_params = os.path.join(pkg, 'config', 'nav2_params.yaml')

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
            ('/model/mars_rover/cmd_vel', '/cmd_vel'),
            ('/model/mars_rover/odometry', '/odom'),
            ('/model/mars_rover/tf', '/tf'),
        ],
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

    lidar_tf_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0',
                   'mars_rover/lidar_link',
                   'mars_rover/lidar_link/lidar_sensor'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    map_static = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'mars_rover/odom'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    odom_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0',
                   'mars_rover/odom',
                   'odom'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        parameters=[{
            'use_sim_time': use_sim_time,
            'yaml_filename': map_file
        }],
        output='screen'
    )

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
        output='screen'
    )

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
        output='screen'
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
        output='screen'
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
        output='screen'
    )

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        parameters=[nav2_params, {'use_sim_time': use_sim_time}],
        output='screen'
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': True,
            'node_names': [
                'map_server',
                'amcl',
                'controller_server',
                'planner_server',
                'behavior_server',
                'bt_navigator',
            ]
        }],
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
            bridge,
            chassis_to_lidar,
            lidar_tf_alias,
            #odom_alias,
            #map_static,
            map_server,
            amcl,
            controller_server,
            planner_server,
            behavior_server,
            bt_navigator,
            lifecycle_manager,
            rviz,
        ]),
    ])
