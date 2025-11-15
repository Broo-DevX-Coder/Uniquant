import logging

# Exception classes for main module ==============================
class RequestCodeError(Exception):
    """Exception raised for errors during request code processing."""

    def __init__(self, request_error):
        self.request_error = request_error
        # Log the exception construction for debugging and telemetry
        logging.error(f"RequestCodeError initialized: {request_error}")

    def __str__(self):
        return f"Request code error >> {self.request_error}" 
    
class UnknownError(Exception):
    """ Exeption for Unknown errors """
    def __init__(self,error):
        self.error = error
        logging.error(f"UnknownError initialized: {error}")

    def __str__(self):
        return f"Unknown Error >> {self.error}"
    
class ValueError(Exception):
    """ Exeption for value incorrect in functions """
    def __init__(self,error):
        self.error = error
        logging.error(f"ValueError (custom) initialized: {error}")

    def __str__(self):
        return f"Value Error >> {self.error}"

# Connection related exceptions ==============================
class Error429(Exception):
    """Exception for HTTP 429 Too Many Requests"""
    def __init__(self, request_info=None):
        self.request_info = request_info
        # Rate limiting is severe: mark as critical
        logging.critical(f"Error429 initialized: {request_info}")

    def __str__(self):
        return f"{self.request_info} -> ⚠️ Too many requests (429). Please wait just 1 minute to retry\nif you dont wait, you IP ADress will blocked"

class Error418(Exception):
    """Exception for HTTP 418 IP Banned Temporarily"""
    def __init__(self, request_info=None):
        self.request_info = request_info
        # IP ban is severe — log as critical
        logging.critical(f"Error418 initialized: {request_info}")

    def __str__(self):
        return f"{self.request_info} ->🚫 IP is banned temporarily (418). Please wait 1 hour to retry\nif you dont wait, you IP ADress will blocked"

class Error403(Exception):
    """Exception for HTTP 403 Forbidden"""
    def __init__(self, request_info=None):
        self.request_info = request_info
        # Forbidden access — log as error
        logging.error(f"Error403 initialized: {request_info}")

    def __str__(self):
        return f"{self.request_info} ❌ Forbidden (403). Your IP might be blocked. Please Try to use VPN or Proxy server"

class ConnectionError(Exception):
    """Exception for No Internet Connection"""
    def __init__(self, request_info=None):
        self.request_info = request_info
        # No internet is critical for connectivity — log as critical
        logging.critical(f"ConnectionError initialized: {request_info}")

    def __str__(self):
        return f"{self.request_info} ❌ No Internet Connection\nPlease Try to connect and retry"

class WebSocketClosedError(Exception):
    """Exception for WebSocket Connection Closed"""
    def __init__(self, request_info=None):
        self.request_info = request_info
        # Websocket closed — log as error for visibility
        logging.error(f"WebSocketClosedError initialized: {request_info}")

    def __str__(self):
        return f"{self.request_info} ❌ WebSocket connection closed\nPlease try reconnecting"
    
