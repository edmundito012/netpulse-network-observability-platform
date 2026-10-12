FROM debian:12-slim

RUN apt-get update \
    && apt-get install \
        --yes \
        --no-install-recommends \
        snmp \
        snmpd \
    && rm -rf /var/lib/apt/lists/*

COPY snmpd.conf /etc/snmp/snmpd.conf

EXPOSE 1161/udp

CMD ["snmpd", "-f", "-Lo", "-C", "-c", "/etc/snmp/snmpd.conf"]