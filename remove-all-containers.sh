#!/bin/bash

#list all containers
containers=$(docker ps -a -q)

if [ -n "$containers" ]; then
    echo "Removing all containers.."
    docker rm -f $containers
else
    echo "No containers to remove."
fi
