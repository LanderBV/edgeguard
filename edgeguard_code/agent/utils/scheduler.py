import csv
import logging
import os
from datetime import datetime
from time import sleep

import numpy as np
import pandas as pd
import psutil
from utils.check_data import Alerts
from utils.extract import Extract
from utils.messaging import MessageFactory
from utils.models import Message
from utils.prediction import Prediction
from utils.influx_class import InfluxDBWriter

LOGGER = logging.getLogger(__name__)


class Scheduler:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance
    

    def run():
        LOGGER.info("Starting Main Loop")
        a = Alerts()
        p = Prediction()
        m = MessageFactory().get_engine(engine="logger")
        i = InfluxDBWriter()
        epoch = 0
        while True:
            # sleep(3)
            epoch += 1
            current_metrics = Extract().get()
            try:              
                future_metrics, drift, error_metric_dict = p.next(metrics=current_metrics)
                a.check_prediction(future_metrics.data)
                message = Message(current=current_metrics.data, future=future_metrics.data, drift=drift)
                m.publish(message=message)
                
                # g.append_data(current_metrics, future_metrics, epoch, error_metric)
                i.write_json(current_metrics, "current_data")
                i.write_json(future_metrics, "future_data")
                i.write_error_metric(current_metrics.timestamp, error_metric_dict)

            except IndexError as e:
                LOGGER.warning(f"Not enough values to make a prediction: {e}")
