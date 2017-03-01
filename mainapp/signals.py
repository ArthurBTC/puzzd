from django.dispatch import Signal

my_signal = Signal(providing_args=["instance", "args", "kwargs"])
beginSignal = Signal(providing_args=["instance", "args", "kwargs"])
stopSignal = Signal(providing_args=["instance", "args", "kwargs"])