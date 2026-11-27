# Data Exfiltration
## [RB-EXFIL-01] Detection indicators
Large outbound transfer volume from an internal host to an external destination, far above the normal baseline, often at unusual hours. Uploads to unfamiliar cloud storage, file sharing sites or foreign IP addresses. Compressed or encrypted archives sent over HTTPS, FTP or SFTP.
## [RB-EXFIL-02] Containment actions
Isolate the source host from the network and block the external destination. Suspend the user account involved. Preserve network flow records and host logs as evidence.
## [RB-EXFIL-03] Impact assessment
Identify which files and data classifications left the network. Notify the data protection officer and legal team if personal or confidential data is involved. Start the breach notification process when required.
