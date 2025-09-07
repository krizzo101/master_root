"""Gunicorn configuration for production deployment."""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv("WORKER_PROCESSES", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.getenv("WORKER_CONNECTIONS", "1000"))
max_requests = int(os.getenv("WORKER_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("WORKER_MAX_REQUESTS_JITTER", "50"))
timeout = int(os.getenv("WORKER_TIMEOUT", "30"))
graceful_timeout = int(os.getenv("WORKER_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("WORKER_KEEPALIVE", "2"))

# Restart workers after this many seconds
max_requests_jitter = 50

# Threading
threads = int(os.getenv("WORKER_THREADS", "2"))

# Process naming
proc_name = "sleuth-intel"

# Logging
accesslog = os.getenv("ACCESS_LOG", "-")
errorlog = os.getenv("ERROR_LOG", "-")
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# StatsD integration (optional)
if os.getenv("STATSD_HOST"):
    statsd_host = os.getenv("STATSD_HOST", "localhost:8125")
    statsd_prefix = "sleuth_intel"

# Server mechanics
daemon = False
pidfile = os.getenv("PID_FILE", "/var/run/sleuth-intel.pid")
user = os.getenv("WORKER_USER", None)
group = os.getenv("WORKER_GROUP", None)
tmp_upload_dir = os.getenv("TMP_UPLOAD_DIR", "/tmp")

# SSL/TLS
if os.getenv("SSL_CERT") and os.getenv("SSL_KEY"):
    keyfile = os.getenv("SSL_KEY")
    certfile = os.getenv("SSL_CERT")
    ssl_version = 3  # TLS
    cert_reqs = 0
    ca_certs = os.getenv("SSL_CA_CERTS", None)
    ciphers = "TLSv1.2"


# Server hooks
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    worker.log.debug(f"Response status: {resp.status}")


def child_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker exited (pid: {worker.pid})")


def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker {worker.pid} exited")


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")


def on_exit(server):
    """Called just before exiting."""
    server.log.info("Server is shutting down")
