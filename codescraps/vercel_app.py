from subprocess import Popen
import os

def app(environ, start_response):
    # Start Streamlit process
    process = Popen(
        ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
    )
    
    # Return response
    start_response("200 OK", [("Content-Type", "text/html")])
    return [b"Streamlit app is running"] 