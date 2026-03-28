"""Lazy access to :mod:`netbox_cli.cli` factories so tests can patch ``cli._get_client`` etc."""

from __future__ import annotations


def get_bound_client():
    from netbox_cli.cli import _get_client

    return _get_client()


def get_bound_index():
    from netbox_cli.cli import _get_index

    return _get_index()
