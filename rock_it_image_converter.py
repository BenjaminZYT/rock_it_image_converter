import dash
from dash import dcc, html, Input, Output, State, ctx
import os
import io
import base64
from PIL import Image
from pillow_heif import register_heif_opener
from flask import send_from_directory

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
        multiple=False  # Allow one file at a time for conversion
    ),
    html.Div(id='uploaded-files-list', style={'margin': '10px', 'color': 'blue'}),
    html.Label("Select output format:"),
    dcc.Dropdown(
        id='output-format',
        options=[{'label': ext.upper(), 'value': ext} for ext in extensions],
        placeholder="Select a file format",
    ),
    html.Button("Convert and Download", id='convert-button', n_clicks=0),
    html.Button("Reset", id='reset-button', n_clicks=0, style={'margin-left': '10px', 'backgroundColor': 'red', 'color': 'white'}),
    html.Div(id='conversion-status'),
    html.P(
        "Created by Benjamin Zu Yao Teoh - Atlanta, GA - January 2025",
        style={'fontSize': '7px', 'textAlign': 'center', 'marginTop': '20px'}
    )
])

# Callback for file upload, conversion, and resetting
@app.callback(
    [Output('uploaded-files-list', 'children'),
     Output('conversion-status', 'children')],
    [Input('convert-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    [State('upload-image', 'contents'),
     State('upload-image', 'filename'),
     State('output-format', 'value')],
    prevent_initial_call=True
)
def handle_image_operations(convert_clicks, reset_clicks, contents, filename, output_format):
    triggered_id = ctx.triggered_id

    if triggered_id == 'reset-button':
        return "", ""

    if triggered_id == 'convert-button' and contents:
        if not contents or not output_format:
            return "", html.Div("Please upload a file and select an output format.", style={'color': 'red'})

        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            image = Image.open(io.BytesIO(decoded))

            base_filename = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base_filename}.{output_format}")

            if output_format.lower() in ["jpg", "jpeg"] and image.mode == "RGBA":
                image = image.convert("RGB")

            save_format = "JPEG" if output_format.lower() in ["jpg", "jpeg"] else output_format.upper()
            image.save(output_path, save_format)

            return "", dcc.Location(href=f"/download/{os.path.basename(output_path)}", id="redirect")

        except Exception as e:
            return "", html.Div(f"Failed to convert {filename}: {str(e)}", style={'color': 'red'})

    return "", ""

# Route for downloading files
@app.server.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(output_dir, filename, as_attachment=True)

if __name__ == '__main__':
    app.run_server(debug=False)
