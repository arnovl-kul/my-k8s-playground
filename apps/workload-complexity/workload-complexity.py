import kubernetes
from datetime import datetime
from influxdb import InfluxDBClient

INFLUXDB_HOST = '172.19.133.29'
INFLUXDB_PORT = 30421

influxClient = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT) 

kubernetes.config.load_kube_config()

v1 = kubernetes.client.CoreV1Api()

list_cpu_usage_server = []
list_cpu_usage_expected = []

ret = v1.list_namespaced_pod(watch=False, namespace='gold')

consumer_pod_list = [[s.metadata.name, ret.items[0].spec.containers[0].resources.requests['cpu']] for s in ret.items if s.metadata.name.startswith("consumer")]

total_cpu_cores = sum([ int(pod_info[1][:-1]) for pod_info in consumer_pod_list])

req_rate = 0

def ru_strategy():
    req_rate*60
    different_configs = set([s[1] for s in consumer_pod_list])
    r = sum([((req_rate*60)/len(different_configs)) * calculate_workload_complexity() * get_latest_ideal_throughput_value(s[1]) for s in consumer_pod_list]) / different_configs
    return r


def calculate_workload_complexity():
    return sum(list_cpu_usage_server) / sum(list_cpu_usage_expected)
        

def get_latest_ideal_throughput_value(cpu_limit):
    it_query = 'SELECT "throughput" \
                        FROM "gold-app-data"."autogen"."idealThroughput" \
                        WHERE "cpu" = \''+ cpu_limit + '\' \
                        ORDER BY time DESC LIMIT 3'
    influxClient.switch_database("gold-app-data")
    results = influxClient.query(it_query)
    return sum([c[1] for c in results.raw['series'][0]['values']]) / len([c[1] for c in results.raw['series'][0]['values']])

for pod_info in consumer_pod_list:
    cpu_query = 'SELECT "pod_name", "value" \
                        FROM "k8s"."default"."cpu/usage_rate" \
                        WHERE "pod_name" = \'' + pod_info[0] + '\' \
                            AND "namespace_name" = \'gold\' \
                            AND time > now() - 1m'   
    mem_query = 'SELECT "pod_name", "value" \
                    FROM "k8s"."default"."cpu/usage" \
                    WHERE "pod_name" = \'' + pod_info[0] + '\' \
                        AND "namespace_name" = \'gold\' \
                        AND time > now() - 1m'   
    req_rate_query = 'SELECT "userCount", "rps", "medianRespTime" \
                        FROM "gold-app-data"."autogen"."responseData" \
                        WHERE time > now() - 1m' 

    results = influxClient.query(cpu_query)
    list_cpu_usage = [c[2] for c in results.raw['series'][0]['values']]

    results = influxClient.query(mem_query)
    list_mem_usage = [c[2] for c in results.raw['series'][0]['values']]

    influxClient.switch_database("gold-app-data")
    results = influxClient.query(req_rate_query)
    list_req_rate = [c[2] for c in results.raw['series'][0]['values']]

    avg_cpu_p_usage = (sum(list_cpu_usage) / len(list_cpu_usage)) / int(pod_info[1][:-1])
    avg_mem_usage = sum(list_mem_usage) / len(list_mem_usage)
    avg_req_rate = sum(list_req_rate) / len(list_req_rate)

    req_rate = avg_req_rate

    ideal_throughput = get_latest_ideal_throughput_value(pod_info[1])

    cpu_usage_expected = avg_req_rate*60*(int(pod_info[1][:-1]) / total_cpu_cores) * ideal_throughput
    
    list_cpu_usage_server.append(avg_cpu_p_usage)
    list_cpu_usage_expected.append(cpu_usage_expected)

print("Workload complexity: " + str(calculate_workload_complexity()))
print("Number of different configs: " + str(len(set([s[1] for s in consumer_pod_list]))))
print("RU_Strategy: " + str(ru_strategy()))