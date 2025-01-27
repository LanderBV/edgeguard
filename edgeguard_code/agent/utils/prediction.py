import itertools
import logging
from datetime import datetime, timedelta
import copy
from icecream import ic
from river import drift, linear_model, metrics, multioutput, preprocessing, compose,feature_extraction, stats, evaluate, time_series
from utils.extract import Extract
from utils.models import Drift, Metrics, Data, Containers

LOGGER = logging.getLogger(__name__)
ic.configureOutput(outputFunction=lambda s: LOGGER.debug(s))


class Prediction:
    def __init__(self):
        self.model_template=(
            time_series.SNARIMAX(
                p=1,
                d=0,
                q=1,
                m=1440,
                sp=1,
                sd=1,
                sq=1,
                regressor=(
                    preprocessing.StandardScaler() |
                    linear_model.LinearRegression()
                    )
                )
            )
        self.model={}
        self.horizon = 1440
   
        
        self.error_metrics = {
            'global': {'mae': metrics.multioutput.MicroAverage(metrics.MAE()), 'rmse': metrics.multioutput.MicroAverage(metrics.RMSE()), 'mape': metrics.multioutput.MicroAverage(metrics.MAPE())},
            'cpu': {'mae': metrics.MAE(), 'rmse': metrics.RMSE(), 'mape': metrics.MAPE()},
            'memory': {'mae': metrics.MAE(), 'rmse': metrics.RMSE(), 'mape': metrics.MAPE()},
            'battery_percent': {'mae': metrics.MAE(), 'rmse': metrics.RMSE(), 'mape': metrics.MAPE()},
            'disk_usage': {'mae': metrics.MAE(), 'rmse': metrics.RMSE(), 'mape': metrics.MAPE()},
            'temperature': {'mae': metrics.MAE(), 'rmse': metrics.RMSE(), 'mape': metrics.MAPE()}
        }
        
        self.drift_detector_cpu = drift.ADWIN(min_window_length=20)
        self.drift_detector_memory = drift.ADWIN(min_window_length=20)
        self.drift_detector_battery = drift.ADWIN(min_window_length=20)
        self.drift_detector_disk_usage = drift.ADWIN(min_window_length=20)

        self.drift_cpu = 0
        self.drift_memory = 0
        self.drift_battery = 0
        self.drift_disk_usage = 0
        
        self.predictions = {}
        self.initialize()


    def initialize(self):
        for name in ['cpu',  'memory', 'battery_percent', 'disk_usage', 'temperature']:
            self.model[name] = copy.deepcopy(self.model_template)

        # Valores actuales del dispositivo
        x = {'datetime': 0.0}
        y = {'cpu': 0, 'memory': 0, 'battery_percent':0, 'disk_usage': 0, 'temperature': 0}
        containers = Extract().containers_deployed()
        for container in containers:  
            y[container.name+"_cpu"]=0
            y[container.name+"_memory"]=0

        for name, model in self.model.items():
            model.learn_one(y[name])

    def drift_calculation(self, y):
        # Check data drift
        self.drift_detector_cpu.update(y['cpu'])
        self.drift_detector_memory.update(y['memory'])
        self.drift_detector_battery.update(y['battery_percent'])
        self.drift_detector_disk_usage.update(y['disk_usage'])

        self.drift_cpu = 0
        self.drift_memory = 0
        self.drift_battery = 0
        self.drift_disk_usage = 0
        
        if self.drift_detector_cpu.drift_detected:
            LOGGER.warning('Drift detected CPU')
            self.drift_cpu = 1

        if self.drift_detector_memory.drift_detected:
            LOGGER.warning('Drift detected MEMORY')
            self.drift_memory = 1

        if self.drift_detector_battery.drift_detected:
            LOGGER.warning('Drift detected Battery')
            self.drift_battery = 1
        
        if self.drift_detector_disk_usage.drift_detected:
            LOGGER.warning('Drift detected Disk')
            self.drift_disk_usage = 1


        return Drift(cpu=self.drift_cpu, memory = self.drift_memory, battery = self.drift_battery, disk_usage = self.drift_disk_usage)
    


    def get_metrics(self, metrics:Metrics):
        y = {'cpu':metrics.data.cpu,
             'memory':metrics.data.memory, 
             'battery_percent':metrics.data.battery_percent, 
             'disk_usage': metrics.data.disk_usage, 
             'temperature': metrics.data.temperature
        }
        if metrics.data.containers:
            for container in metrics.data.containers:
                y[container.name+"_cpu"]=container.cpu
                y[container.name+"_memory"]=container.memory

        return y

    def learn(self, metrics: Metrics):      
        y = self.get_metrics(metrics)
        # Learn actual device status
        for name, model in self.model.items():
            model.learn_one(y[name])
        

    def next(self, metrics: Metrics):
        # Future timestamp for prediction
        timestamp_datetime = datetime.fromtimestamp(metrics.timestamp)
        future_datetime = timestamp_datetime + timedelta(minutes=self.horizon)
        
        y = self.get_metrics(metrics)
        
        # Learn actual device status and predict in horizon
        y_preds = {}
        for name, model in self.model.items():
            y_preds[name] =  model.forecast(horizon=self.horizon)[-1]
        self.learn(metrics)
        # Calculate drift
        # drift=self.drift_calculation(y)
        drift = Drift(cpu=0, memory = 0, battery = 0, disk_usage = 0)
        # Update the error metric
        self.append_data(timestamp_datetime,y,future_datetime, y_preds)
        
        return Metrics(timestamp=future_datetime.timestamp(), data=self.create_data_object(y_preds)), drift, self.error_metrics

    def append_data(self, time, y, time_pred, y_pred):
        self.predictions[time_pred]=y_pred
        if time in self.predictions:
            self.update_metrics(y,self.predictions[time])
            del self.predictions[time]
                

    def update_metrics(self, y, y_pred):
        for key, metric in self.error_metrics.items():
            if key == 'global':
                actual = y
                predicted = y_pred
            else: 
                actual = y.get(key, 0.0)
                predicted = y_pred.get(key, 0.0)

            # Actualizar MAE
            metric['mae'].update(actual, predicted)
            
            # Actualizar RMSE
            metric['rmse'].update(actual, predicted)
            
            # Actualizar R²
            metric['mape'].update(actual, predicted)
 
    def create_data_object(self, data_dict):
        containers = []
        for key, value in data_dict.items():
            if key.endswith('_cpu'):
                name = key[:-4]
                container = Containers(name=name, cpu=value, memory=data_dict.get(key.replace('_cpu', '_memory'), 0.0))
                containers.append(container)

        return Data(
            cpu=data_dict.get('cpu', 0.0),
            memory=data_dict.get('memory', 0.0),
            battery_percent=data_dict.get('battery_percent', 0.0),
            disk_usage=data_dict.get('disk_usage', 0.0),
            temperature=data_dict.get('temperature', 0.0),
            containers=containers if containers else None
        )

    def get_drift(self) -> Metrics:
        pass
