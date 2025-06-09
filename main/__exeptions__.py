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