# Library import review — release v26.9

## Finding

**Severity: critical.** The package could install and start Robot Framework, but
the public short-name import exposed no keywords in the reported environment.
This invalidated all delivered examples at suite setup and teardown.

## Correction review

- The public class is now defined in the `BK8500Library` module.
- It inherits the complete decorated implementation without duplicating logic.
- A dry-run Robot suite verifies discovery of `Open Load Connection`,
  `Close All Load Connections`, and `Get Load Product Information`.
- Environment selection rejects an interpreter where this smoke suite fails.
- Python tests assert the shim ownership and inherited keyword metadata.

## Residual risk

The packaging environment does not provide Robot Framework from its internal
package mirror, so full runtime execution must also be confirmed on the user's
installed Robot Framework environment. The correction follows the documented
class-library import model and is protected by the delivered dry-run gate.

## Decision

Approved for package release v26.9. Hardware verification remains open.
