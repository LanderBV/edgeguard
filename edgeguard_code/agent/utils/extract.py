import psutil
from utils.models import Metrics, Containers
from datetime import datetime
import docker

class Extract:
    def __init__(self): 
        self.timestamp= datetime.now().timestamp()
        self.cpu = psutil.getloadavg()[0]
        # self.cpu = psutil.cpu_percent(interval=0.5)
        self.memory = psutil.virtual_memory().percent
        self.battery_percent = psutil.sensors_battery().percent
        self.disk_usage = psutil.disk_usage('/').percent
        self.temperature = self.get_temperature()
        self.containers = self.container_metrics_to_list()
        self.metric = Metrics(timestamp=self.timestamp, data={'cpu': self.cpu, 'memory': self.memory, 'battery_percent': self.battery_percent,
                                                               'disk_usage': self.disk_usage, 'temperature': self.temperature, 'containers': self.containers})

    def is_container_running(self, container_name):
        client = docker.from_env()
        try:
            container = client.containers.get(container_name)
            return container.status == "running"
        except docker.errors.NotFound:
            return False

    def containers_deployed(self):
        containers_list=[]
        containers = docker.DockerClient().containers.list(all=True)
        for c in containers:
            container_name = c.name
            if self.is_container_running(container_name):
                containers_list.append(c)
        return containers_list

    def container_metrics_to_list(self):
        container_metric_list = []
        try:
            containers = self.containers_deployed()
            for container in containers:
                status = container.stats(stream = False)
                try:
                    # Calculate the cpu usage of the container taking in to account the amount of cores the CPU has
                    cpu_delta = status["cpu_stats"]["cpu_usage"]["total_usage"] - status["precpu_stats"]["cpu_usage"]["total_usage"]
                    system_delta = status["cpu_stats"]["system_cpu_usage"] - status["precpu_stats"]["system_cpu_usage"]
                    cpuPercent = (cpu_delta / system_delta) * (status["cpu_stats"]["online_cpus"]) * 100
                    # Fetch the memory consumption for the container
                    memory_stats = status['memory_stats']
                    memory_usage = memory_stats['usage']
                    memory_limit = memory_stats['limit']
                    # Memory percentage
                    mem = memory_usage*100/memory_limit
                    container_metric_list.append(Containers(name=container.name, cpu=cpuPercent, memory=mem))
                except Exception as e:
                    print("Error: " + str(e))
                    break
            return container_metric_list
        except Exception as e:
            print("Error: "+str(e))
            pass



    def get_temperature(self):
        cpu_temperature = psutil.sensors_temperatures().get('coretemp')
        try:
            return cpu_temperature[0].current
        except Exception as e:
            print("Error: " + str(e))

    
    def get(self) -> Metrics:
        return self.metric



