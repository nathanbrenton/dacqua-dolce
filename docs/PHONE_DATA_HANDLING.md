# D'Acqua Dolce — Phone Data Handling

Customer-facing phone fields accept digit-only entry and add presentation
formatting automatically. Typing `9495551234` renders `(949) 555-1234`.

Frontend formatting is usability only. FastAPI independently validates the
submitted value and normalizes valid US/NANP numbers to E.164, for example
`+19495551234`.

The backend rejects letters, extensions embedded in the field, unexpected
characters, invalid lengths, area codes beginning with 0 or 1, and exchanges
beginning with 0 or 1.

P0 phone support is deliberately US/NANP. International support should later
use country selection and a vetted international phone-number parser instead
of weakening current validation.
