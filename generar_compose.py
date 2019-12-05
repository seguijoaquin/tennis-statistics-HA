#!/usr/bin/env python
import argparse
import sys
import yaml
import os

# basedirname = os.path.split(os.getcwd())[-1] # docker-compose image prefix
basedirname = os.path.split(os.getcwd())[-1].lower().rstrip()

templates = {
    "date_filter": """
  date_filter_{0}:
    build:
      context: .
      dockerfile: date_filter/Dockerfile
    environment:
      HOSTNAME: date_filter_{0}
    command: python3 -u ./date_filter.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "date_filter_terminator": """
  date_filter_terminator_{0}:
    build:
      context: .
      dockerfile: terminator/Dockerfile
    environment:
      PROCESSES_NUMBER: {DATE_FILTERS_NUMBER}
      IN_EXCHANGE: date_filter_terminator
      GROUP_EXCHANGE: matches
      GROUP_EXCHANGE_TYPE: fanout
      GROUP_ROUTING_KEY: ''
      NEXT_EXCHANGE: filtered
      NEXT_EXCHANGE_TYPE: direct
      NEXT_ROUTING_KEYS: dispatcher-joiner
      HOSTNAME: date_filter_terminator_{0}
    command: python3 -u ./terminator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "surface_dispatcher": """
  surface_dispatcher_{0}:
    build:
      context: .
      dockerfile: surface_dispatcher/Dockerfile
    command: python3 -u ./surface_dispatcher.py
    environment:
      HOSTNAME: surface_dispatcher_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "surface_dispatcher_terminator": """
  surface_dispatcher_terminator_{0}:
    build:
      context: .
      dockerfile: terminator/Dockerfile
    environment:
      PROCESSES_NUMBER: {SURFACE_DISPATCHERS_NUMBER}
      IN_EXCHANGE: dispatcher_terminator
      GROUP_EXCHANGE: filtered
      GROUP_EXCHANGE_TYPE: direct
      GROUP_ROUTING_KEY: dispatcher
      NEXT_EXCHANGE: surfaces
      NEXT_EXCHANGE_TYPE: direct
      NEXT_ROUTING_KEYS: Hard-Clay-Grass
      HOSTNAME: surface_dispatcher_terminator_{0}
    command: python3 -u ./terminator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "hard_accumulator": """
  hard_accumulator_{0}:
    build:
      context: .
      dockerfile: accumulator/Dockerfile
    environment:
      ROUTING_KEY: Hard
      EXCHANGE: surfaces
      OUTPUT_EXCHANGE: surface_values
      HOSTNAME: hard_accumulator_{0}
    command: python3 -u ./accumulator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "clay_accumulator": """
  clay_accumulator_{0}:
    build:
      context: .
      dockerfile: accumulator/Dockerfile
    environment:
      ROUTING_KEY: Clay
      EXCHANGE: surfaces
      OUTPUT_EXCHANGE: surface_values
      HOSTNAME: clay_accumulator_{0}
    command: python3 -u ./accumulator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "grass_carpet_accumulator": """
  grass_carpet_accumulator_{0}:
    build:
      context: .
      dockerfile: accumulator/Dockerfile
    environment:
      ROUTING_KEY: Grass-Carpet
      EXCHANGE: surfaces
      OUTPUT_EXCHANGE: surface_values
      HOSTNAME: grass_carpet_accumulator_{0}
    command: python3 -u ./accumulator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "average_calculator": """
  average_calculator_{0}:
    build:
      context: .
      dockerfile: average_calculator/Dockerfile
    command: python3 -u ./average_calculator.py
    environment:
      HOSTNAME: average_calculator_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "joiner": """
  joiner_{0}:
    build:
      context: .
      dockerfile: joiner/Dockerfile
    command: python3 -u ./joiner.py
    environment:
      HOSTNAME: joiner_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "joiner_terminator": """
  joiner_terminator_{0}:
    build:
      context: .
      dockerfile: terminator/Dockerfile
    environment:
      PROCESSES_NUMBER: {JOINERS_NUMBER}
      IN_EXCHANGE: joiner_terminator
      GROUP_EXCHANGE: filtered
      GROUP_EXCHANGE_TYPE: direct
      GROUP_ROUTING_KEY: joiner
      NEXT_EXCHANGE: joined
      NEXT_EXCHANGE_TYPE: direct
      NEXT_ROUTING_KEYS: filter-calculator
      HOSTNAME: joiner_terminator_{0}
    command: python3 -u ./terminator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "age_calculator": """
  age_calculator_{0}:
    build:
      context: .
      dockerfile: age_calculator/Dockerfile
    command: python3 -u ./age_calculator.py
    environment:
      HOSTNAME: age_calculator_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "age_calculator_terminator": """
  age_calculator_terminator_{0}:
    build:
      context: .
      dockerfile: terminator/Dockerfile
    environment:
      PROCESSES_NUMBER: {AGE_CALCULATORS_NUMBER}
      IN_EXCHANGE: calculator_terminator
      GROUP_EXCHANGE: joined
      GROUP_EXCHANGE_TYPE: direct
      GROUP_ROUTING_KEY: calculator
      NEXT_EXCHANGE: player_age
      NEXT_EXCHANGE_TYPE: fanout
      NEXT_ROUTING_KEYS: ''
      HOSTNAME: age_calculator_terminator_{0}
    command: python3 -u ./terminator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "age_difference_filter": """
  age_difference_filter_{0}:
    build:
      context: .
      dockerfile: age_difference_filter/Dockerfile
    command: python3 -u ./age_difference_filter.py
    environment:
      HOSTNAME: age_difference_filter_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "age_difference_filter_terminator":"""
  age_difference_filter_terminator_{0}:
    build:
      context: .
      dockerfile: terminator/Dockerfile
    environment:
      PROCESSES_NUMBER: {AGE_DIFFERENCE_FILTERS_NUMBER}
      IN_EXCHANGE: age_filter_terminator
      GROUP_EXCHANGE: player_age
      GROUP_EXCHANGE_TYPE: fanout
      GROUP_ROUTING_KEY: ''
      NEXT_EXCHANGE: database
      NEXT_EXCHANGE_TYPE: direct
      NEXT_ROUTING_KEYS: age
      HOSTNAME: age_difference_filter_terminator_{0}
    command: python3 -u ./terminator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "different_hands_filter": """
  different_hands_filter_{0}:
    build:
      context: .
      dockerfile: different_hands_filter/Dockerfile
    command: python3 -u ./different_hands_filter.py
    environment:
      HOSTNAME: different_hands_filter_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "different_hands_filter_terminator":"""
  different_hands_filter_terminator_{0}:
    build:
      context: .
      dockerfile: terminator/Dockerfile
    environment:
      PROCESSES_NUMBER: {DIFFERENT_HANDS_FILTERS_NUMBER}
      IN_EXCHANGE: hands_filter_terminator
      GROUP_EXCHANGE: joined
      GROUP_EXCHANGE_TYPE: direct
      GROUP_ROUTING_KEY: filter
      NEXT_EXCHANGE: hands
      NEXT_EXCHANGE_TYPE: direct
      NEXT_ROUTING_KEYS: R-L
      HOSTNAME: different_hands_filter_terminator_{0}
    command: python3 -u ./terminator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "right_accumulator":"""
  right_accumulator_{0}:
    build:
      context: .
      dockerfile: accumulator/Dockerfile
    environment:
      ROUTING_KEY: R
      EXCHANGE: hands
      OUTPUT_EXCHANGE: hands_values
      HOSTNAME: right_accumulator_{0}
    command: python3 -u ./accumulator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "left_accumulator":"""
  left_accumulator_{0}:
    build:
      context: .
      dockerfile: accumulator/Dockerfile
    environment:
      ROUTING_KEY: L-U
      EXCHANGE: hands
      OUTPUT_EXCHANGE: hands_values
      HOSTNAME: left_accumulator_{0}
    command: python3 -u ./accumulator.py
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "percentage_calculator": """
  percentage_calculator_{0}:
    build:
      context: .
      dockerfile: percentage_calculator/Dockerfile
    command: python3 -u ./percentage_calculator.py
    environment:
      HOSTNAME: percentage_calculator_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "client":"""
  client_{0}:
    build:
      context: .
      dockerfile: client/Dockerfile
    environment:
      HOSTNAME: client_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "database":"""
  database_{0}:
    build:
      context: .
      dockerfile: database/Dockerfile
    command: python3 -u ./database.py
    environment:
      HOSTNAME: database_{0}
    depends_on:
      rabbitmq:
        condition: service_healthy
""",
    "watchdog":"""
  watchdog_{0}:
    build:
      context: .
      dockerfile: watchdog/Dockerfile
    command: python3 -u ./watchdog.py
    environment:
      HOSTNAME: watchdog_{0}
      PID: {0}
      BASEDIRNAME: {basedirname}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      rabbitmq:
        condition: service_healthy
"""
}
header = """
version: '2.4'
services:
  rabbitmq:
    image: rabbitmq:3.7.14-management
    ports:
      - '15672:15672'
    healthcheck:
      test: [ "CMD", "rabbitmq-diagnostics", "-q", "check_port_connectivity"]
      interval: 5s
      timeout: 40s
      retries: 10
"""


if __name__ == "__main__":
    cluster_config = {}
    with open("cluster_config.yml", "r") as f:
        cluster_config = yaml.safe_load(f)

    with open("docker-compose.yml", "w") as f:
        f.write(header)
        for key in templates.keys():
            amount = 1 if key not in cluster_config else cluster_config[key]
            for i in range(amount):
                f.write(templates[key].format(i,
                  basedirname=basedirname,
                  DATE_FILTERS_NUMBER=cluster_config["date_filter_terminator"],
                  SURFACE_DISPATCHERS_NUMBER=cluster_config["surface_dispatcher"],
                  AGE_CALCULATORS_NUMBER=cluster_config["age_calculator"],
                  AGE_DIFFERENCE_FILTERS_NUMBER=cluster_config["age_difference_filter"],
                  DIFFERENT_HANDS_FILTERS_NUMBER=cluster_config["different_hands_filter"],
                  JOINERS_NUMBER=cluster_config["joiner"]))
