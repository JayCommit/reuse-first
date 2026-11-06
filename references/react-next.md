# React / Next.js example

Request: add a customer picker to the invoice form.

Search both domain and UI terms: `CustomerPicker`, `EntitySelect`, `Combobox`,
`customer`, and another form with a remote lookup. Inspect the form's existing
validation and loading/error states as well as the shared component's props and
callers. Check whether the target is a server or client component before reusing
hooks or adding imports.

Suppose `src/components/EntitySelect.tsx` supports typed options, keyboard
navigation, and a loading state, and `src/customers/useCustomerOptions.ts` already
fetches the options. Compose those in the invoice form. Avoid a fresh picker
with its own fetch call, dropdown styles, and keyboard handling.

Example evidence before editing:

> `EntitySelect.tsx` already implements the selection behavior; its supplier-form
> caller shows the form integration. I will reuse it with `useCustomerOptions`
> and the invoice form's validation pattern.

If the shared select only accepts a small static list and the task needs server
pagination, inspect other async selects first. A separate wrapper may be smaller
than changing all static callers. Explain that contract difference, then reuse
the applicable primitives. Required Next.js route files should follow a nearby
route's auth, validation, and error conventions rather than duplicating a client.

Verify selection, loading/failure behavior, keyboard access, and existing shared
component callers when its contract changes. The paths above are illustrative;
replace them with files actually found in the target codebase.
