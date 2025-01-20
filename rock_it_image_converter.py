import dash
from dash import dcc, html, Input, Output, State, ctx
import os
import io
import base64
from PIL import Image
from pillow_heif import register_heif_opener
from flask import Flask, send_file
import time

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
    html.Audio(id='audio-player', src='', controls=False, autoPlay=True, style={'display': 'none'}),
    html.Div(id='uploaded-files-list', style={'margin': '10px', 'color': 'blue'}),
    html.Label("Select output format:"),
    dcc.Dropdown(
        id='output-format',
        options=[{'label': ext.upper(), 'value': ext} for ext in extensions],
        placeholder="Select a file format",
    ),
    html.Button("Convert and Download", id='convert-button', n_clicks=0),
    html.Button("Reset", id='reset-button', n_clicks=0, style={'margin-left': '10px', 'backgroundColor': 'red', 'color': 'white'}),
    html.Div(id='conversion-status', style={'margin-top': '20px', 'color': 'green'}),
    dcc.Location(id='redirect', refresh=True),
    html.P(
        "Created by Benjamin Zu Yao Teoh - Atlanta, GA - January 2025",
        style={'fontSize': '7px', 'textAlign': 'center', 'marginTop': '20px'}
    )
])

# Callback for handling upload, conversion, download, and reset
@app.callback(
    [Output('uploaded-files-list', 'children'),
     Output('conversion-status', 'children'),
     Output('redirect', 'href'),
     Output('audio-player', 'src')],
    [Input('convert-button', 'n_clicks'),
     Input('reset-button', 'n_clicks'),
     Input('upload-image', 'contents')],
    [State('upload-image', 'filename'),
     State('output-format', 'value')],
    prevent_initial_call=True
)
def handle_conversion_and_download(convert_clicks, reset_clicks, contents, filename, output_format):
    triggered_id = ctx.triggered_id

    if triggered_id == 'reset-button':
        # Clear all outputs on reset
        return "", "", None, None

    if triggered_id == 'upload-image' and contents:
        audio_src = "https://www.voicy.network/Content/Clips/Sounds/2022/10/9e13b434-b0f4-4cf7-85b1-0a8eb75e06f9.mp3"  # Clip from "I Feel Good"
        return f"Uploaded file: {filename}", "", None, audio_src

    if triggered_id == 'convert-button' and contents:
        if not contents or not output_format:
            return "", "Please upload a file and select an output format.", None, None

        try:
            # Decode the uploaded file
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            image = Image.open(io.BytesIO(decoded))

            # Prepare output file path
            base_filename = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base_filename}.{output_format}")

            # Convert RGBA to RGB if saving as JPEG
            if output_format.lower() in ['jpg', 'jpeg'] and image.mode == 'RGBA':
                image = image.convert('RGB')

            save_format = 'JPEG' if output_format.lower() in ['jpg', 'jpeg'] else output_format.upper()
            image.save(output_path, save_format)

            # Generate the download link
            download_href = f"/download/{os.path.basename(output_path)}"
            return f"File uploaded: {filename}", "Converted file downloaded!", download_href, None

        except Exception as e:
            return "", f"Failed to convert {filename}: {str(e)}", None, None

    return "", "", None, None

# Route for downloading files
@app.server.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(output_dir, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run_server(debug=False)
