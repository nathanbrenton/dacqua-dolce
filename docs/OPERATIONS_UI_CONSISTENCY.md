# D'Acqua Dolce — Operations UI Consistency

A pricing-policy update was correctly committed to PostgreSQL, but the same
request could return the previously loaded `product.prices` relationship from
SQLAlchemy's identity map. This made the selector visually revert until the
browser refreshed.

The operations product reload now uses
`execution_options(populate_existing=True)`, so the post-write response
replaces already-loaded ORM state with the committed pricing records.
