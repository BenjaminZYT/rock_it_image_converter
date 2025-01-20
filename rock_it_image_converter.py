import os
import base64
import io
from PIL import Image
from pillow_heif import register_heif_opener

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context, exceptions

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
    Output('converted-image-container', 'children'),
    Output('conversion-message', 'children'),
    Input('upload-image', 'contents'),
    State('upload-image', 'filename'),
    State('upload-image', 'last_modified'),
    Input('reset-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_app(content, filename, last_modified, n_clicks):
    """
    1) On file upload, store base64 data in dcc.Store.
    2) Show success/fail messages.
    3) On 'Reset', clear everything and return initial state.
    """
    ctx = callback_context
    if not ctx.triggered:
        raise exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # If reset was clicked, empty everything
    if trigger_id == "reset-button":
        return (
            {'filename': None, 'content': None},  # Clear store
            "",  # upload-message
            "",  # converted-image-container
            ""   # conversion-message
        )

    # Handle file upload
    if content is not None:
        try:
            # We won't do the actual image opening here; just store it in memory
            return (
                {'filename': filename, 'content': content},
                f'Uploaded: "{filename}"',
                "",  # no preview or message yet
                ""
            )
        except Exception as e:
            return (
                {'filename': None, 'content': None},
                f'Upload failed: {str(e)}',
                "",
                ""
            )

    # If no content triggered and it wasn't reset, do nothing
    raise exceptions.PreventUpdate


@app.callback(
    Output('converted-image-container', 'children'),
    Output('conversion-message', 'children'),
    Output('download-image', 'data'),  # Triggers the file download
    Input('convert-button', 'n_clicks'),
    State('upload-store', 'data'),
    State('output-format', 'value')
)
def convert_and_download(n_clicks, upload_data, output_format):
    """
    Convert the stored image to the selected format, display a preview,
    and automatically download the converted file.
    """
    if not n_clicks:
        raise exceptions.PreventUpdate

    # Check if user has uploaded a file
    if not upload_data or not upload_data['content']:
        return "", "Please upload an image first.", None

    # Check if a format is selected
    if not output_format:
        return "", "Please select an output format.", None

    try:
        # Decode the stored image from base64
        content_type, content_string = upload_data['content'].split(',')
        decoded = base64.b64decode(content_string)
        image = Image.open(io.BytesIO(decoded))

        # Convert the image in memory
        converted = io.BytesIO()
        # The format argument to PIL should be uppercase: 'JPEG', 'PNG', etc.
        pil_format = output_format.upper()
        image.save(converted, format=pil_format)
        converted.seek(0)

        # Make a base64 string for preview
        encoded_image = base64.b64encode(converted.read()).decode('utf-8')
        data_url = f"data:image/{output_format};base64,{encoded_image}"

        # Reset the in-memory buffer for the actual file download
        converted.seek(0)

        # Prepare the file download
        # We'll pick a filename like "converted.png", "converted.jpg", etc.
        download_filename = f"converted.{output_format}"
        download_data = dcc.send_bytes(
            converted.read(),
            filename=download_filename
        )

        preview_image = html.Img(src=data_url, style={'max-width': '500px'})

        return preview_image, "File has been downloaded!", download_data

    except Exception as e:
        return "", f"Conversion failed: {str(e)}", None


if __name__ == "__main__":
    # On Render, you often need to bind to 0.0.0.0 and a given port from the env
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
