"""Catchy ML workspace.

Trains the phishing classifier that complements the M2 rule engine. The guiding
constraint (see _backend.py): featurization reuses the *production* parser and
FeatureExtractor, so the model learns from the exact numbers it will score on.
"""
