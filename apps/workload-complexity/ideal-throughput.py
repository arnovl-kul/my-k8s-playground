import kubernetes
from influxdb import InfluxDBClient

INFLUXDB_HOST = '172.19.133.29'
INFLUXDB_PORT = 30421

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
                        AND time > now() - 1h'   
    mem_query = 'SELECT "pod_name", "value" \
                    FROM "k8s"."default"."cpu/usage" \
                    WHERE "pod_name" = \'' + pod_info[0] + '\' \
                        AND "namespace_name" = \'gold\' \
                        AND time > now() - 1h'   
    req_rate_query = 'SELECT "userCount", "rps", "medianRespTime" \
                        FROM "gold-app-data"."autogen"."responseData" \
                        WHERE "pod_name" = \'' + pod_info[0] + '\' \
                            AND "namespace_name" = \'gold\' \
                            AND time > now() - 1h'   

    influxClient.switch_database("k8s")

    results = influxClient.query(cpu_query)
    list_cpu_usage = [c[2] for c in results.raw['series'][0]['values']]

    results = influxClient.query(mem_query)
    list_mem_usage = [c[2] for c in results.raw['series'][0]['values']]

    influxClient.switch_database("gold-app-data")

    results = influxClient.query(mem_query)
    list_req_rate = [c[2] for c in results.raw['series'][0]['values']]

    avg_cpu_p_usage = (sum(list_cpu_usage) / len(list_cpu_usage)) / int(pod_info[1][:-1])
    avg_mem_usage = sum(list_mem_usage) / len(list_mem_usage)
    avg_req_rate = sum(list_req_rate) / len(list_req_rate)

    basic_ideal_throughput = avg_cpu_p_usage / ( (avg_req_rate * 3600) * (int(pod_info[1][:-1]) / total_cpu_cores) )

    influxClient.switch_database("gold-app-data")

    time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    json_body = [{
        "measurement": "idealThroughput",
        "time": time,
        "tags": {
            "podName": pod_info[0],
            "cpu": pod_info[1]
        },
        "fields": {
            "throughput": basic_ideal_throughput
        }
    }]
    influxClient.write_points(json_body)

    print(pod_info[0] + "(" + pod_info[1] + ") : " + basic_ideal_throughput)
