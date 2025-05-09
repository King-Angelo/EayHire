# myproject/middleware.py

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # get the response (must be HttpResponse object)
        response = self.get_response(request)

        # Check that response is an HttpResponse before setting headers
        if hasattr(response, '__setitem__'):  # safe check for HttpResponse-like object
            # Add security headers
            response['X-Frame-Options'] = 'DENY'
            response['X-Content-Type-Options'] = 'nosniff'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=()'

            # More permissive CSP for development
            if request.META.get('DEVELOPMENT', 'True') == 'True':
                response['Content-Security-Policy'] = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' https://cdnjs.cloudflare.com; "
                    "connect-src 'self'; "
                    "frame-src 'self'; "
                    "object-src 'none'"
                )
            else:
                response['Content-Security-Policy'] = "default-src 'self'"

        return response
