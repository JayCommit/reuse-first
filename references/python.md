# Python example

Request: add a command that fetches an account's invoices with retries.

Search `invoice`, `account`, `client`, `retry`, `timeout`, and an existing command
that calls the same service. Inspect the client constructor, auth, pagination,
exception types, and CLI error presentation. Check package exports and tests.

Suppose `billing/client.py` owns the HTTP session and retry policy, and
`commands/accounts.py` demonstrates argument parsing and error rendering. Add
the smallest invoice method to the client and use it from the command, following
the existing command structure. Do not introduce another HTTP session or retry
loop in the CLI.

Example evidence before editing:

> `billing/client.py` owns authenticated requests and retries; I will extend it
> with invoice pagination and follow `commands/accounts.py` for CLI errors.

If an existing helper is synchronous and the task requires an async service,
inspect async clients before reusing it. Blocking the event loop or wrapping the
entire sync client may violate the contract. Explain a new client's boundary and
reuse compatible serialization or domain types without coupling to private code.

Verify the new behavior through the project's HTTP mocking approach and check
representative callers if changing shared exceptions or defaults. These filenames
are examples, not claims about the target repository.
