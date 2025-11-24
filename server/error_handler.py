from .config import DATA_DIR, AUDIT_LOG, now_ts

def log(message: str) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG, 'a', encoding='utf-8') as af:
            af.write(f"{now_ts()} {message}\n")
    except Exception:
        # best-effort logging; swallow errors to avoid crashing server
        pass

def log_exception(exc: Exception, prefix: str = '') -> None:
    log(f"{prefix}{exc!r}")
