import kubernetes
from datetime import datetime
from influxdb import InfluxDBClient

INFLUXDB_HOST = '172.19.133.29'
INFLUXDB_PORT = 30421

def normalize_list(list_t):
    return [ (s - min(list_t)) / (max(list_t) - min(list_t)) for s in list_t]

def ideal_throughput_current():
    influxClient = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT) 

    kubernetes.config.load_kube_config()

    v1 = kubernetes.client.CoreV1Api()

    ret = v1.list_namespaced_pod(watch=False, namespace='gold')

    consumer_pod_list = [[s.metadata.name, ret.items[0].spec.containers[0].resources.requests['cpu']] for s in ret.items if s.metadata.name.startswith("consumer")]

    total_cpu_cores = sum([ int(pod_info[1][:-1]) for pod_info in consumer_pod_list])

    for pod_info in consumer_pod_list:
        cpu_query = 'SELECT "pod_name", "value" \
                        FROM "k8s"."default"."cpu/usage_rate" \
                        WHERE "pod_name" = \'' + pod_info[0] + '\' \
                            AND "namespace_name" = \'gold\' \
                            AND time > now() - 10m'   
        mem_query = 'SELECT "pod_name", "value" \
                        FROM "k8s"."default"."memory/usage" \
                        WHERE "pod_name" = \'' + pod_info[0] + '\' \
                            AND "namespace_name" = \'gold\' \
                            AND time > now() - 10m'   
        req_rate_query = 'SELECT "userCount", "rps", "medianRespTime" \
                            FROM "gold-app-data"."autogen"."responseData" \
                            WHERE time > now() - 10m'   

        influxClient.switch_database("k8s")

        results = influxClient.query(cpu_query)
        list_cpu_usage = [c[2] for c in results.raw['series'][0]['values']]

        results = influxClient.query(mem_query)
        list_mem_usage = [c[2] for c in results.raw['series'][0]['values']]
        list_mem_usage = normalize_list(list_mem_usage)

        influxClient.switch_database("gold-app-data")
        
        results = influxClient.query(req_rate_query)
        list_req_rate = [c[2] for c in results.raw['series'][0]['values']]

        avg_cpu_p_usage = (sum(list_cpu_usage) / len(list_cpu_usage)) / int(pod_info[1][:-1])
        avg_mem_usage = sum(list_mem_usage) / len(list_mem_usage)
        avg_req_rate = sum(list_req_rate) / len(list_req_rate)

        print("Average memory usage (normalized): " + str(avg_mem_usage))

        basic_ideal_throughput = avg_cpu_p_usage / ( (avg_req_rate * 600) * (int(pod_info[1][:-1]) / total_cpu_cores) )

        mem_ideal_throughput = [ s / ( (avg_req_rate * 600) * (int(pod_info[1][:-1]) / total_cpu_cores) ) for s in [avg_mem_usage, avg_cpu_p_usage]]

        influxClient.switch_database("gold-app-data")

        time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        json_body = [{
            "measurement": "idealThroughput",
            "time": time[0],
            "tags": {
                "podName": pod_info[0],
                "cpu": pod_info[1]
            },
            "fields": {
                "basic-throughput": basic_ideal_throughput,
                "extended-throughput-mem": mem_ideal_throughput[0],
                "extended-throughput-cpu": mem_ideal_throughput[1]
            }
        }]
        influxClient.write_points(json_body)

        print("Avg cpu usage: " + str(avg_cpu_p_usage))
        print("Percentage of total: " + str(int(pod_info[1][:-1])/total_cpu_cores))
        print("Req rate: " + str(avg_req_rate))
        print(pod_info[0] + "(" + pod_info[1] + ") : basic: " + str(basic_ideal_throughput))
        print(pod_info[0] + "(" + pod_info[1] + ") : mem: " + str(mem_ideal_throughput[0]))
        print(pod_info[0] + "(" + pod_info[1] + ") : cpu: " + str(mem_ideal_throughput[1]))

ideal_throughput_current()
