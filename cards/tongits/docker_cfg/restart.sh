#!/bin/bash
port=$1

./close_single_port_sudo.sh $port

sleep 5

./start_server.sh