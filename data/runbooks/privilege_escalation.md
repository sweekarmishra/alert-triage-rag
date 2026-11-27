# Privilege Escalation and Lateral Movement
## [RB-PRIV-01] Detection indicators
A normal user account suddenly gains administrator or root rights, or is added to a privileged group. Use of sudo, su or token manipulation by an account that never did so before. Lateral logins to many servers using the same account, or execution of credential dumping tools.
## [RB-PRIV-02] Containment actions
Disable the affected account and revoke active sessions and tokens. Isolate the host where the escalation happened. Remove unauthorized group memberships and scheduled tasks.
## [RB-PRIV-03] Follow-up
Review the audit log to find how the privileges were obtained. Patch the exploited local vulnerability or fix the misconfiguration. Rotate secrets and passwords reachable from the compromised account.
