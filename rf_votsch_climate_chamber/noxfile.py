import nox

@nox.session(python=["3.11", "3.12", "3.13"])
def tests(session):
    session.install("-e", ".[dev]")
    session.run("pytest", "--cov=rf_votsch_climate_chamber", "--cov-branch")

@nox.session(python="3.11")
def metadata(session):
    session.install("-e", ".[dev]")
    session.run("python", "scripts/validate_structure.py")
    session.run("python", "scripts/validate_ai_contract.py")
    session.run("python", "scripts/validate_call_protocol_conformance.py")
