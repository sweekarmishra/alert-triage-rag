# SQL Injection Against Web Applications
## [RB-SQLI-01] Detection indicators
HTTP requests whose parameters contain SQL syntax such as UNION SELECT, OR 1=1, comment markers, quote characters or time delay functions like SLEEP. Web server returns database errors or unusually large responses. Repeated payload variations from one client suggest an automated tool such as sqlmap.
## [RB-SQLI-02] Containment actions
Block the source IP and enable the web application firewall SQL injection ruleset. Disable or restrict the vulnerable endpoint until it is patched. Rotate database credentials used by the application.
## [RB-SQLI-03] Remediation
Replace string concatenation with parameterized queries. Review database logs for unauthorized reads or writes. Audit what data the application account can access and reduce its privileges.
