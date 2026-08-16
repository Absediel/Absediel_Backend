from rest_framework.throttling import SimpleRateThrottle

class EmailRateThrottle(SimpleRateThrottle):
    scope = 'email'

    def get_cache_key(self, request, view):
        if request.method != 'POST':
            return None
        
        # Check email from POST payload
        email = request.data.get('email')
        if not email:
            return None
        
        # Unique key per email
        return self.cache_format % {
            'scope': self.scope,
            'ident': email.strip().lower()
        }
