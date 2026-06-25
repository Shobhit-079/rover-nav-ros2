cmake_minimum_required(VERSION 3.8)
project(rover_nav)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  launch
  worlds
  models
  config
  maps
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
