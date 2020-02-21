#!/usr/bin/env python

import json


def read_config():
    with open("config.json") as json_file:
        config = json.load(json_file)
        check_name = config["check_name"]
        check_description = config["check_description"]
        dashboard_style = config["dashboard_style"]
        slab_style = config["slab_style"]
        frequency = config["frequency"].split("_")

    overseer_file = "checks/" + check_name + "-" + check_description + ".json"

    return check_name, check_description, dashboard_style, slab_style, frequency, overseer_file
