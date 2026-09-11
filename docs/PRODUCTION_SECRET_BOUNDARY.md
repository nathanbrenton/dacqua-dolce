# D'Acqua Dolce — Production Secret Boundary

The public Git repository may contain configuration templates and variable
names, but never populated production secrets.

Production-only values include:

- PostgreSQL passwords;
- Postmark server token;
- AWS/S3 credentials;
- TLS private keys;
- backup encryption credentials;
- session/cryptographic secrets if introduced;
- deployment private keys;
- infrastructure API tokens.

Production secrets belong in root-controlled runtime configuration outside the
repository.

The application must never print secrets during startup diagnostics or include
them in health/readiness responses.
