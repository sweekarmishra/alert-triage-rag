# Malware Command and Control Beaconing
## [RB-C2-01] Detection indicators
An internal host connects to the same external IP or domain at regular fixed intervals with small, uniform payload sizes. Low jitter in connection timing, long running sessions to rare destinations, or traffic on unusual ports. The destination matches threat intelligence for known command and control servers.
## [RB-C2-02] Containment actions
Isolate the infected host and block the command and control domain and IP at the firewall and DNS. Capture memory and disk images before remediation. Reset credentials that were used on the host.
## [RB-C2-03] Eradication
Run endpoint detection scans to find the implant and persistence mechanisms. Hunt for the same beacon pattern on other hosts. Reimage the host if the malware cannot be removed with confidence.
