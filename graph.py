# graph.py
import csv
import os
from graphviz import Digraph
import PyPDF2

def generate_graphs_from_csv(
    csv_file: str,
    output_dir: str = "static",
    prefix: str = "handler_graph",
    merge_pdf: bool = True
):
    """
    Reads the CSV of call handler menu entries, creates a PNG (and optionally PDF)
    per call handler, merges into a single PDF if requested, and returns
    a dictionary describing the generated files:

    {
      "png_files": [...just the file paths...],
      "pdf_files": [...],
      "merged_pdf": "handler_graph_combined.pdf" or None,
      "png_mapping": [
         {
           "handlerName": "Sales",
           "pngFile": "handler_graph_images/Sales.png"
         },
         ...
      ]
    }
    """

    os.makedirs(output_dir, exist_ok=True)

    # Group rows by call handler
    call_handlers = {}
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ch_name = row["CallHandlerName"]
            call_handlers.setdefault(ch_name, []).append(row)

    # We'll track each generated file
    png_files = []
    pdf_files = []
    png_mapping = []  # List of {"handlerName": <>, "pngFile": <>}

    subfolder = os.path.join(output_dir, prefix + "_images")
    os.makedirs(subfolder, exist_ok=True)

    for ch_name, entries in call_handlers.items():
        dot = Digraph(name=ch_name)

        # Main node
        call_handler_id = f"CH_{ch_name}"
        dot.node(
            call_handler_id,
            label=f"Call Handler:\n{ch_name}",
            shape="box",
            style="filled",
            fillcolor="#cfe2f3"
        )

        # Sub-nodes
        for entry in entries:
            touchtone = entry["TouchtoneKey"] or "(none)"
            action_desc = entry["ActionDescription"] or "(none)"
            transfer_num = entry["TransferNumber"] or ""
            disp_name = entry["MenuEntryDisplayName"] or ""

            label_lines = [
                f"Touchtone: {touchtone}",
                f"Action: {action_desc}"
            ]
            if transfer_num:
                label_lines.append(f"Transfer#: {transfer_num}")
            if disp_name:
                label_lines.append(f"DisplayName: {disp_name}")

            node_label = "\n".join(label_lines)
            sub_node_id = f"{call_handler_id}_{touchtone}"

            dot.node(
                sub_node_id,
                label=node_label,
                shape="box",
                style="filled",
                fillcolor="#f8f9fa"
            )
            dot.edge(call_handler_id, sub_node_id)

        # Create filenames
        safe_ch_name = ch_name.replace(" ", "_").replace("/", "_")
        png_filename = f"{safe_ch_name}.png"
        pdf_filename = f"{safe_ch_name}.pdf"
        png_path = os.path.join(subfolder, png_filename)
        pdf_path = os.path.join(subfolder, pdf_filename)

        # Render PNG
        dot.render(
            filename=os.path.splitext(png_path)[0],
            format="png",
            cleanup=True
        )
        png_files.append(os.path.join(prefix + "_images", png_filename))

        # Map the handler name to the PNG path
        png_mapping.append({
            "handlerName": ch_name,
            "pngFile": os.path.join(prefix + "_images", png_filename)
        })

        # Render PDF (if we want individual PDFs as well)
        dot.render(
            filename=os.path.splitext(pdf_path)[0],
            format="pdf",
            cleanup=True
        )
        pdf_files.append(os.path.join(prefix + "_images", pdf_filename))

    # Merge PDFs if requested
    merged_pdf_path = None
    if merge_pdf and pdf_files:
        merged_pdf_path = os.path.join(output_dir, f"{prefix}_combined.pdf")
        merge_pdfs([os.path.join(output_dir, f) for f in pdf_files], merged_pdf_path)

    return {
        "png_files": png_files,
        "pdf_files": pdf_files,
        "merged_pdf": os.path.basename(merged_pdf_path) if merged_pdf_path else None,
        "png_mapping": png_mapping
    }

def merge_pdfs(pdf_list, output_pdf):
    merger = PyPDF2.PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_pdf)
    merger.close()
