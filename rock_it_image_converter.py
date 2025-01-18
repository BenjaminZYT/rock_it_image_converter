import dash
from dash import dcc, html, Input, Output, State
import os
import io
import base64
from PIL import Image
from pillow_heif import register_heif_opener

# Register HEIF opener
register_heif_opener()

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server

# Create a directory for storing converted images
output_dir = "converted_images"
os.makedirs(output_dir, exist_ok=True)

# Supported extensions
extensions = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif']

# Layout of the Dash app
app.layout = html.Div([
    html.H1("Image Converter"),
    html.Label("Upload an image to convert:"),
    dcc.Upload(
        id='upload-image',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True
    ),
    html.Label("Select output format:"),
    dcc.Dropdown(
        id='output-format',
        options=[{'label': ext.upper(), 'value': ext} for ext in extensions],
        placeholder="Select a file format",
    ),
    html.Button("Convert and Download", id='convert-button', n_clicks=0),
    html.Div(id='conversion-status'),
    html.Div(id='download-links', style={'margin-top': '20px'})
])

# Callback for file upload and conversion
@app.callback(
    [Output('conversion-status', 'children'),
     Output('download-links', 'children')],
    [Input('convert-button', 'n_clicks')],
    [State('upload-image', 'contents'),
     State('upload-image', 'filename'),
     State('output-format', 'value')]
)
def convert_and_download(n_clicks, contents, filenames, output_format):
    if n_clicks == 0 or not contents or not output_format:
        return "", ""

    conversion_status = []
    download_links = []

    for content, filename in zip(contents, filenames):
        try:
            # Decode the uploaded file
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            image = Image.open(io.BytesIO(decoded))

            # Prepare output filename and path
            base_filename = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base_filename}.{output_format}")

            # Convert RGBA to RGB if saving as JPEG
            if output_format.lower() in ["jpg", "jpeg"] and image.mode == "RGBA":
                image = image.convert("RGB")

            # Save the image in the selected format
            save_format = "JPEG" if output_format.lower() in ["jpg", "jpeg"] else output_format.upper()
            image.save(output_path, save_format)

            # Add to conversion status and download links
            conversion_status.append(f"Successfully converted {filename} to {output_format.upper()}.")
            download_link = html.A(
                f"Download {os.path.basename(output_path)}",
                href=f"/download/{os.path.basename(output_path)}",
                target="_blank"
            )
            download_links.append(html.Div(download_link))

        except Exception as e:
            conversion_status.append(f"Failed to convert {filename}: {str(e)}")

    return html.Div(conversion_status), html.Div(download_links)

# Route for downloading files
@app.server.route('/download/<filename>')
def download_file(filename):
    from flask import send_from_directory
    return send_from_directory(output_dir, filename, as_attachment=True)

if __name__ == '__main__':
    app.run_server(debug=False)