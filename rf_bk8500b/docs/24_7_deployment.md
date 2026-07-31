# 24/7 deployment and monitoring

Version 0.1.0 is an implementation candidate, not an endurance-qualified release.

For supervised qualification:

1. Pin a tested driver version and Python runtime.
2. Give one process exclusive ownership of one serial port.
3. Record identity, model, serial, firmware, protocol, adapter, OS, and configuration at startup.
4. Poll `health_check()` and export `diagnostic_snapshot()` after anomalies.
5. Treat three consecutive failures as degraded service.
6. Use bounded application retries only for read-only workflows.
7. Reconcile identity and state after reconnect.
8. Store audit events outside the command thread using a non-blocking sink.
9. Monitor process RSS, handles/file descriptors, thread count, latency, timeout count, and indeterminate outcomes.
10. Stop the production sequence on wrong-device identity, protection trips, recurrent framing errors, or uncertain hazardous commands.

Gate G8 requires a 168-hour hardware soak and at least 1,000 open/close cycles with no meaningful resource leak.
