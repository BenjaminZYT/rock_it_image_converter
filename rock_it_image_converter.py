import os
import base64
import io
from PIL import Image
from pillow_heif import register_heif_opener

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, exceptions

# Enable HEIC/HEIF support for Pillow
register_heif_opener()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Expose the underlying Flask server for gunicorn

app.layout = dbc.Container([
    html.H1("Image Converter"),

    # Hidden store to hold uploaded file info in memory
    dcc.Store(id='upload-store', data={'filename': None, 'content': None}),

    # Download component (for automatic file downloads)
    dcc.Download(id="download-image"),

    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id='upload-image',
                multiple=False,
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select a File')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                }
            ),
            html.Div(id='upload-message', style={'marginTop': '1em', 'color': 'green'}),
        ], width=6),

        dbc.Col([
            dcc.Dropdown(
                id='output-format',
                options=[
                    {'label': 'JPEG', 'value': 'jpeg'},
                    {'label': 'PNG', 'value': 'png'},
                    {'label': 'BMP', 'value': 'bmp'},
                    {'label': 'TIFF', 'value': 'tiff'},
                    {'label': 'GIF', 'value': 'gif'}
                ],
                placeholder="Select Output Format"
            ),
            dbc.Button("Convert and Download", id="convert-button", color="primary", className="mt-3"),
            html.Div(id='conversion-message', style={'marginTop': '1em', 'color': 'blue'}),
        ], width=6)
    ]),

    html.Div(id='converted-image-container', style={'marginTop': '2em'}),

    dbc.Button("Reset", id="reset-button", color="secondary", className="mt-3"),
])

@app.callback(
    Output('upload-store', 'data'),
    Output('upload-message', 'children'),
    Input('upload-image', 'contents'),
    State('upload-image', 'filename'),
    prevent_initial_call=True
)
def handle_upload(content, filename):
    """
    Handles file uploads:
    - Store the uploaded file in the dcc.Store component.
    - Display the uploaded filename in a success message.
    """
    if content is None or filename is None:
        raise exceptions.PreventUpdate

    try:
        # Store file content and filename
        return {'filename': filename, 'content': content}, f'Uploaded: "{filename}" successfully!'
    except Exception as e:
        return {'filename': None, 'content': None}, f'Error: Failed to upload "{filename}". {str(e)}'


@app.callback(
    Output('converted-image-container', 'children'),
    Output('conversion-message', 'children'),
    Output('download-image', 'data'),  # Triggers the file download
    Input('convert-button', 'n_clicks'),
    State('upload-store', 'data'),
    State('output-format', 'value'),
    prevent_initial_call=True
)
def convert_and_download(n_clicks, upload_data, output_format):
    """
    Converts the uploaded image to the selected format and triggers download.
    """
    if n_clicks is None:
        raise exceptions.PreventUpdate

    if not upload_data or not upload_data['content']:
        return "", "Please upload an image first.", None

    if not output_format:
        return "", "Please select an output format.", None

    try:
        # Decode the uploaded file from base64
        content_type, content_string = upload_data['content'].split(',')
        decoded = base64.b64decode(content_string)
        image = Image.open(io.BytesIO(decoded))

        # Convert the image to the chosen format
        converted_image = io.BytesIO()
        image.save(converted_image, format=output_format.upper())
        converted_image.seek(0)

        # Generate a base64 preview for display
        encoded_image = base64.b64encode(converted_image.read()).decode('utf-8')
        data_url = f"data:image/{output_format};base64,{encoded_image}"

        # Prepare the file download
        converted_image.seek(0)
        download_filename = f"converted.{output_format}"
        download_data = dcc.send_bytes(
            converted_image.read(),
            filename=download_filename
        )

        preview_image = html.Img(src=data_url, style={'max-width': '500px'})

        return preview_image, "File has been downloaded successfully!", download_data
    except Exception as e:
        return "", f"Error: Conversion failed. {str(e)}", None


@app.callback(
    Output('upload-store', 'data'),
    Output('upload-message', 'children'),
    Output('converted-image-container', 'children'),
    Output('conversion-message', 'children'),
    Input('reset-button', 'n_clicks'),
    prevent_initial_call=True
)
def reset_app(n_clicks):
    """
    Resets the app to its initial state:
    - Clears the upload store.
    - Clears all messages and image previews.
    """
    if n_clicks:
        return {'filename': None, 'content': None}, "", "", ""


if __name__ == "__main__":
    # Bind to 0.0.0.0 for Render with dynamic port
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
