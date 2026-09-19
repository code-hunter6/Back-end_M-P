from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory limiter is fine for a single process. Behind multiple workers or
# instances, point storage_uri at Redis so the counters are shared:
#   Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
