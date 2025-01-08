# app.py

import os
import uuid
from flask import Flask, render_template, request, Response, send_from_directory
from backend import export_call_handlers_menu_entries_sse
from flask import Flask, render_template, request, send_from_directory, jsonify
from graph import generate_graphs_from_csv

app = Flask(__name__)


@app.route("/")
def index():
	return render_template("index.html")


@app.route("/run_export_sse")
def run_export_sse():
	"""
    SSE endpoint that:
      1. Reads query params (or form data) for base_url, username, password
      2. Calls the generator in backend.py
      3. Streams SSE events to the client
    """
	base_url = f"https://" + request.args.get("base_url", "").strip()
	username = request.args.get("username", "").strip()
	password = request.args.get("password", "").strip()

	# Generate a unique CSV filename
	csv_filename = f"call_handler_menu_entries_{uuid.uuid4().hex}.csv"
	full_path = os.path.join("static", csv_filename)

	def generate():
		try:
			# This calls our generator in backend.py
			for sse_message in export_call_handlers_menu_entries_sse(
					base_url=base_url,
					username=username,
					password=password,
					output_csv=full_path
			):
				yield sse_message
		except Exception as e:
			# If there's an error mid-stream, we can yield an SSE event "error"
			yield f"event: error\ndata: {str(e)}\n\n"

	return Response(generate(), mimetype="text/event-stream")


@app.route("/download_csv/<filename>")
def download_csv(filename):
	"""
    Endpoint to download the CSV from the static folder.
    """
	return send_from_directory("static", filename, as_attachment=True)


@app.route("/generate_graphs")
def generate_graphs():
    csv_filename = request.args.get("csv_filename", "").strip()
    if not csv_filename:
        return jsonify({"error": "No csv_filename provided"}), 400

    csv_path = os.path.join("static", csv_filename)
    if not os.path.exists(csv_path):
        return jsonify({"error": f"CSV file not found: {csv_filename}"}), 404

    result = generate_graphs_from_csv(
        csv_file=csv_path,
        output_dir="static",
        prefix="handler_graph",
        merge_pdf=True
    )
    # Now result has "png_mapping"

    return jsonify(result)


@app.route("/static/<path:filename>")
def serve_static(filename):
	"""
    If you need a route to serve the static files.
    Typically, 'send_from_directory' is used, or you rely on Flask's static_folder.
    """
	return send_from_directory("static", filename)


if __name__ == "__main__":
	os.makedirs("static", exist_ok=True)
	app.run(debug=True, host="0.0.0.0", port=5000)
