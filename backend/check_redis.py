import redis
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    print(f"Queue 'celery' length: {r.llen('celery')}")
except Exception as e:
    print(f"Error: {e}")
