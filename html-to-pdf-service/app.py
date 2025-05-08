# html-to-pdf-service/app.py
import os
import subprocess
import tempfile
import time
import sys
from flask import Flask, request, send_file, jsonify
import traceback

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_html_to_pdf():
    """
    Receives HTML content via POST request, converts it to PDF using wkhtmltopdf,
    and returns the PDF binary data.
    Expects JSON body: {"html": "<div>...</div>"}
    Returns: PDF file binary data (application/pdf) or JSON error message.
    """
    print("Received POST request to /convert")
    sys.stdout.flush() # Force immediate flushing of print statements

    temp_html_file_path = None
    temp_pdf_file_path = None

    try:
        # Get JSON data from the request body
        data = request.get_json()
        if not data or 'html' not in data:
            print("Error: Invalid request body, JSON with 'html' key is required.")
            sys.stdout.flush()
            return jsonify({"error": "Invalid request, JSON body with 'html' key is required"}), 400

        # Extract HTML content
        html_content = data.get('html')
        if not html_content:
            print("Error: 'html' key is present but value is empty or null.")
            sys.stdout.flush()
            return jsonify({"error": "'html' key is present but value is empty or null"}), 400

        # Print a snippet of the received HTML for debugging
        print(f"Received HTML content (first 200 chars): {html_content[:200]}...")
        sys.stdout.flush()

        # Create secure temporary files for HTML input and PDF output
        # mkstemp returns a file descriptor (int) and a path (str).
        # We need the path, so we close the descriptor immediately after getting it.
        temp_html_fd, temp_html_file_path = tempfile.mkstemp(suffix=".html")
        os.close(temp_html_fd) # Close the descriptor as we'll use the path with subprocess
        temp_pdf_fd, temp_pdf_file_path = tempfile.mkstemp(suffix=".pdf")
        os.close(temp_pdf_fd) # Close the descriptor

        print(f"Created temp files: {temp_html_file_path}, {temp_pdf_file_path}")
        sys.stdout.flush()

        # Write the received HTML content to the temporary HTML file
        # Specify utf-8 encoding to match the input HTML
        with open(temp_html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Wrote HTML to {temp_html_file_path}")
        sys.stdout.flush()

        # Command to run wkhtmltopdf
        # xvfb-run is used to run wkhtmltopdf in a virtual display buffer,
        # which is necessary in headless environments like Docker containers.
        # --auto-servernum and --server-args configure xvfb.
        # --encoding utf-8 tells wkhtmltopdf the input file encoding.
        # --enable-local-file-access might be needed if your HTML references local files (CSS, images).
        command = [
            'xvfb-run', # Run in a virtual display buffer
            '--auto-servernum', # Automatically assign a server number
            '--server-args="-screen 0, 1024x768x24"', # Set screen resolution for xvfb
            'wkhtmltopdf',
            '--encoding', 'utf-8', # <-- ADDED: Explicitly set input encoding to UTF-8
            '--enable-local-file-access', # Often needed if your HTML links local CSS/images
            # '--debug-javascript', # Uncomment if you suspect JS issues related to JS rendering
            # '--no-outline', # Example option: Removes PDF outline
            # '--page-size', 'A4', # Example option: Set page size
            # '--margin-top', '10mm', # Example option: Set margins
            temp_html_file_path, # Input HTML file path (the temporary file we created)
            temp_pdf_file_path   # Output PDF file path (the temporary file for the result)
        ]

        print(f"Running command: {' '.join(command)}")
        sys.stdout.flush()

        # Execute the wkhtmltopdf command
        # capture_output=True captures stdout/stderr of the subprocess.
        # text=True decodes stdout/stderr as text (using default encoding, but wkhtmltopdf errors are usually ASCII).
        result = subprocess.run(command, capture_output=True, text=True)

        print(f"Command finished with return code: {result.returncode}")
        sys.stdout.flush()
        print("wkhtmltopdf STDOUT:\n", result.stdout)
        sys.stdout.flush()
        print("wkhtmltopdf STDERR:\n", result.stderr)
        sys.stdout.flush()

        # Check if the conversion was successful (wkhtmltopdf typically returns 0 on success)
        if result.returncode != 0:
            print("PDF conversion failed according to wkhtmltopdf return code.")
            sys.stdout.flush()
            # Return a 500 response with details from wkhtmltopdf's stderr and stdout
            return jsonify({
                "error": "PDF conversion failed",
                "details": result.stderr,
                "command_output": result.stdout # Include stdout too for completeness
            }), 500

        # Check if the PDF output file was actually created and is not empty
        if not os.path.exists(temp_pdf_file_path) or os.path.getsize(temp_pdf_file_path) == 0:
             print("PDF conversion command succeeded (return code 0), but output file was not created or is empty.")
             sys.stdout.flush()
             return jsonify({
                "error": "PDF conversion command succeeded, but output file is missing or empty",
                "details": f"Output file path: {temp_pdf_file_path}",
                "command_output_stderr": result.stderr,
                "command_output_stdout": result.stdout
             }), 500

        # If successful, read the generated PDF file and send it back in the HTTP response
        print(f"Reading PDF from {temp_pdf_file_path} for sending.")
        sys.stdout.flush()
        # send_file is a Flask utility that efficiently streams the file content.
        # mimetype='application/pdf' is crucial for the client (n8n) to handle the data correctly.
        # as_attachment=True suggests a download filename, though n8n consumes the binary data directly.
        return send_file(
            temp_pdf_file_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='converted.pdf' # Default filename
        )

    except Exception as e:
        # Catch any unexpected Python errors during the process
        print(f"An unexpected internal error occurred: {e}")
        sys.stdout.flush()
        # Print the full traceback to standard output for debugging in Docker logs
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        # Return a 500 response with the error details
        return jsonify({"error": f"An internal server error occurred: {e}"}), 500

    finally:
        # Ensure temporary files are cleaned up regardless of success or failure
        print("Cleaning up temporary files...")
        sys.stdout.flush()
        # Remove the temporary HTML file
        if temp_html_file_path and os.path.exists(temp_html_file_path):
            try:
                os.remove(temp_html_file_path)
                print(f"Removed {temp_html_file_path}")
            except OSError as e:
                print(f"Error removing temporary html file {temp_html_file_path}: {e}")
            sys.stdout.flush()

        # Remove the temporary PDF file
        if temp_pdf_file_path and os.path.exists(temp_pdf_file_path):
             try:
                os.remove(temp_pdf_file_path)
                print(f"Removed {temp_pdf_file_path}")
             except OSError as e:
                print(f"Error removing temporary pdf file {temp_pdf_file_path}: {e}")
             sys.stdout.flush()

        print("Cleanup finished.")
        sys.stdout.flush()


# Entry point for the Flask development server
# This block runs when the script is executed directly (e.g., by `flask run`).
# In production, you would typically use a production-ready WSGI server like Gunicorn
# (add 'gunicorn' to requirements.txt and use a Gunicorn CMD in the Dockerfile).
if __name__ == '__main__':
    # app.run() starts the development server.
    # host='0.0.0.0' makes the server accessible from any IP, including other Docker containers on the same network.
    # port=5000 is the port the server listens on.
    # debug=True is useful for development but should be False in production.
    app.run(host='0.0.0.0', port=5000)
