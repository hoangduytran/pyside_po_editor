def safe_emit_signal(signal, *args):
    try:
        signal.emit(*args)
    except RuntimeError:
        # Signal source was deleted → ignore
        pass
