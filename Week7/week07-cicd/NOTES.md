# NOTES.md — Week 7: CI/CD Integration Testing

**Student ID used with `generate_for_student.py`:**
142301017

## Why gate integration-test on needs: [lint, unit-test]?

Integration tests take more time since they need to build a Docker image and start a container. So, I used 'needs: [lint, unit-test]' to make sure the linting and unit tests pass first. This way, if there is already an issue in the basic checks, we don't waste time running the Docker-based integration tests.
