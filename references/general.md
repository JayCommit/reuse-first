# General codebases

Search by three views of the requested behavior:

| View | Example terms | What to inspect |
| --- | --- | --- |
| Domain | invoice, account, customer | Existing service and its consumers |
| Capability | pagination, retry, selector | Utilities, components, adapters |
| Convention | error, validation, logging | A maintained neighboring implementation |

Start in the relevant package, then check shared packages and another likely
owner. Find declarations and usages with native tools if the optional indexer
does not recognize the language. Search results do not prove code is maintained
or safe to import.

For example, a Go endpoint may already use a response writer with consistent
error envelopes. A new handler should reuse that writer and follow a nearby
handler's validation and context handling. Check whether a proposed helper is
internal to another package before importing it. In a monorepo, dependency
direction and package APIs matter more than reducing a few lines.

In a new codebase with no comparable implementations, inspect repository
instructions and available scaffolding, report the absence, and implement the
smallest coherent solution. The skill should not manufacture an abstraction or
block authorized work because there is nothing to reuse.
