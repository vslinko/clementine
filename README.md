# paragraph.py is realtime log parser

my nginx config:

    log_format paragraph '$connection $msec $request_time $remote_addr $request_method $scheme://$host$request_uri $status $request_length $bytes_sent';
    access_log /var/log/nginx/paragraph.log paragraph;
