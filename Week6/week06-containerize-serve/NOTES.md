# NOTES.md — Week 6: Containerize and Serve a Detector

**Student ID used with `generate_for_student.py`:**
142301017



## Built image size

<!-- What image size did `docker images` report for week6-detector? -->
234 MB

## Swapping in a real checkpoint

<!-- What's the single biggest thing you'd change about this Dockerfile if
     src/mock_detector.py were swapped for a real torch-based checkpoint?
     (Think about what that does to build time and image size.) -->

If `src/mock_detector.py` were replaced with a real PyTorch checkpoint, I would need to add the PyTorch dependencies and copy the model checkpoint into the image. This would increase the Docker image size and build time significantly.