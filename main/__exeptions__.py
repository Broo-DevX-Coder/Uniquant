# Exception classes for main module ==============================
class RequestCodeError(Exception):
    """Exception raised for errors during request code processing."""

    def __init__(self, request_error):
        self.request_error = request_error

    def __str__(self):
        return f"Request code error >> {self.request_error}" 
    
class UnknownError(Exception):
    """ Exeption for Unknown errors """
    def __init__(self,error):
        self.error = error

    def __str__(self):
        return f"Unknown Error >> {self.error}"
    
class ValueError(Exception):
    """ Exeption for value incorrect in functions """
    def __init__(self,error):
        self.error = error

    def __str__(self):
        return f"Value Error >> {self.error}"

# Connection related exceptions ==============================
class Error429(Exception):
    """Exception for HTTP 429 Too Many Requests"""
    def __init__(self, request_info):
        self.request_info = request_info

    def __str__(self):
        return f"{self.request_info} -> ⚠️ Too many requests (429). Please wait just 1 minute to retry\nif you dont wait, you IP ADress will blocked"

class Error418(Exception):
    """Exception for HTTP 418 IP Banned Temporarily"""
    def __init__(self, request_info):
        self.request_info = request_info

    def __str__(self):
        return f"{self.request_info} ->🚫 IP is banned temporarily (418). Please wait 1 hour to retry\nif you dont wait, you IP ADress will blocked"

class Error403(Exception):
    """Exception for HTTP 403 Forbidden"""
    def __init__(self, request_info):
        self.request_info = request_info

    def __str__(self):
        return f"{self.request_info} ❌ Forbidden (403). Your IP might be blocked. Please Try to use VPN or Proxy server"

class ConnectionError(Exception):
    """Exception for No Internet Connection"""
    def __init__(self, request_info):
        self.request_info = request_info

    def __str__(self):
        return f"{self.request_info} ❌ No Internet Connection\nPlease Try to connect and retry"
    
