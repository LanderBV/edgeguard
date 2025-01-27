import logging

from utils.models import Data



LOGGER = logging.getLogger(__name__)

class Alerts:

    def __init__(self):
        self.thresholds = {'cpu': {'critical': 90,'warning': 70,'info': 50 },
                            'memory': {'critical': 90,'warning': 70,'info': 50 },
                            'battery_percent': {'critical': 10,'warning': 30,'info': 50 },
                            'disk_usage': {'critical': 90,'warning': 70,'info': 50 },
                            'temperature': {'critical': 120,'warning': 100,'info': 70 }
                        }

    def check_prediction(self, data: Data):
        for attr, thresholds in self.thresholds.items():
            value = getattr(data, attr)
            alert_triggered = False
            if attr == 'battery_percent':
                for threshold_type, threshold_value in thresholds.items():
                    if value < threshold_value:
                        self.send_alert(attr, value, threshold_type)
                        alert_triggered = True
                        break
            else:
                for threshold_type, threshold_value in thresholds.items():
                    if value > threshold_value:
                        self.send_alert(attr, value, threshold_type)
                        alert_triggered = True
                        break
            if not alert_triggered:
                LOGGER.warning(f"{attr.capitalize()}: {value} CORRECT")
            
    
    def send_alert(self, attr, value, threshold_type):
        # Create a json with the variables and the predictions

        if threshold_type== "critical":
            LOGGER.critical(f"{attr.capitalize()}: {value} exceeds the {threshold_type.replace('_', ' ')} threshold")
        elif threshold_type=="warning":
            LOGGER.warning(f"{attr.capitalize()}: {value} exceeds the {threshold_type.replace('_', ' ')} threshold")
        else:
            LOGGER.info(f"{attr.capitalize()}: {value} exceeds the {threshold_type.replace('_', ' ')} threshold")