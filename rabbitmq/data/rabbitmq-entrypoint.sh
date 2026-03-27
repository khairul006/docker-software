#!/bin/bash
set -e

# Enable RabbitMQ plugins
rabbitmq-plugins enable rabbitmq_mqtt
rabbitmq-plugins enable rabbitmq_web_mqtt

# Start RabbitMQ server
exec rabbitmq-server