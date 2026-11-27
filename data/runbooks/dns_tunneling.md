# DNS Tunneling
## [RB-DNS-01] Detection indicators
Very high volume of DNS queries from one host to a single domain. Long, random looking subdomain labels with high entropy, and many TXT or NULL record queries. Unusually large DNS response sizes compared to normal lookups.
## [RB-DNS-02] Containment actions
Sinkhole or block the suspicious domain at the DNS resolver. Isolate the host producing the queries. Restrict outbound DNS so hosts may only use approved internal resolvers.
## [RB-DNS-03] Investigation
Decode a sample of the queried subdomains to see what data was carried. Identify the process on the host that generates the queries. Check for other hosts querying the same domain.
