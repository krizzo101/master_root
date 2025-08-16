"""Helper to start celery worker:  python -m code_gen.worker"""

from task_queue import celery

if __name__ == "__main__":
    celery.worker_main()
