#!/bin/bash
iverilog -o traffic_light_sim traffic_light_controller.v tb_traffic_light_controller.v
vvp traffic_light_sim
