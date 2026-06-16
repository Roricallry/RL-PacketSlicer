
服务端执行：
```sh
iperf3 -s
```

##### 带宽测试

###### 1. TCP测试
client->server:
```sh
iperf3 -c <server_IP>
```
server->client
```
iperf3 -c <server_IP> -R
```

###### 2. UDP测试
```
iperf3 -c <server_IP> -u -b 10M【或者1G】
```


##### 参数速查
```
-p <port>：指定端口，默认 5201。

-t <sec>：测试总时长（秒），默认 10 秒。
 
-i <sec>：结果报告间隔时间。

-P <num>：并发线程数。
   
-f [k|m|g]：指定带宽显示单位。例如 -f m 显示为 Mbits/sec。
   
-l <size>：读写缓冲区大小，TCP 默认 128KB。
   
-w <size>：TCP 窗口大小。在测试高延迟网络（长肥网络）时，需要手动增大窗口大小以获得准确带宽。
  
--bidir：双向同时测试
```
