# Distributed Denial of Service
## [RB-DDOS-01] Detection indicators
Sudden spike in inbound packets per second or bandwidth from many distinct source IPs toward a single destination. SYN flood shows a large count of half-open TCP connections and a very low ACK ratio. UDP or ICMP flood shows high volume traffic with tiny or identical payloads. Service latency rises and requests time out.
## [RB-DDOS-02] Mitigation actions
Enable SYN cookies and connection rate limits on the edge firewall. Apply rate limiting or geo filtering to the targeted service. Engage the upstream provider or DDoS scrubbing service to absorb volumetric traffic.
## [RB-DDOS-03] Escalation and recovery
Notify the on-call network team and the service owner. Keep packet captures of the flood for analysis. Scale out the affected service and confirm normal latency before closing the incident.
