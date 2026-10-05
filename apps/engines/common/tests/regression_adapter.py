"""Adapter de pruebas cargado en el proceso hijo, sin GPU."""

import time

from engine_mock import MockAdapter


class SlowLoadAdapter(MockAdapter):
    def load(self, *args):
        time.sleep(2.2)
        super().load(*args)
