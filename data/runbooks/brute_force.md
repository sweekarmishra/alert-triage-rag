# Brute Force Authentication Attack
## [RB-BRUTE-01] Detection indicators
Many failed login attempts for SSH, RDP or web login from one source IP within a short window. Failed logins against many different usernames, or a password spraying pattern, with a high failed-login rate per minute. A successful login right after a long run of failures is a strong sign of compromise.
## [RB-BRUTE-02] Containment actions
Block the offending source IP at the firewall. Enforce account lockout and rate limiting on the authentication service. Force a password reset for any account that logged in successfully after the failures.
## [RB-BRUTE-03] Hardening and follow-up
Disable password authentication for SSH and require key based login or MFA. Review authentication logs for the past 24 hours for the same source. Add the source to the threat intelligence blocklist.
