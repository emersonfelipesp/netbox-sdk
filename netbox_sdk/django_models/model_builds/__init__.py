"""Bundled Django model-build artifacts, read through :mod:`importlib.resources`.

Data only. The reading logic lives in :mod:`netbox_sdk.django_models.catalog`;
this package exists so the artifacts are importable package data rather than
repository-root files that no distribution can carry. Regenerate with
``scripts/build_model_catalog.py``.
"""
