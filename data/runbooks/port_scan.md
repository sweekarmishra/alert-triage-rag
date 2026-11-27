# Network Reconnaissance and Port Scan
## [RB-SCAN-01] Detection indicators
One source IP probing many different destination ports or many hosts in a short time. Connections are mostly SYN with immediate reset or no reply, with very few bytes transferred. Sequential port ordering or sweeping a whole subnet suggests automated scanning tools such as nmap.
## [RB-SCAN-02] Response actions
Block or rate limit the scanning source IP. Check whether any probed port is open that should not be exposed. Verify firewall rules close all unused ports.
## [RB-SCAN-03] Follow-up
Treat internal scanning as higher risk because it may indicate a compromised host performing lateral movement. Correlate the scanner IP with other alerts in the last 24 hours.
