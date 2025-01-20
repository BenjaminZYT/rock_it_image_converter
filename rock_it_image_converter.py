import os
import base64
import io
from PIL import Image
from pillow_heif import register_heif_opener

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context

# Enable HEIC/HEIF support for Pillow
register_heif_opener()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Expose the underlying Flask server for gunicorn/etc.

app.layout = dbc.Container([
    html.H1("Image Converter"),

    # Hidden store to hold uploaded file info in memory
    dcc.Store(id='upload-store', data={'filename': None, 'content': None}),

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
            html.Div(id='upload-message'),
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
            html.Div(id='conversion-message'),
        ], width=6)
    ]),

    html.Div(id='converted-image-container'),
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
    1) Store the uploaded image in dcc.Store
    2) Show success/fail messages
    3) Clear everything on "Reset"
    """
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # If reset was clicked, empty everything
    if trigger_id == "reset-button":
        return {'filename': None, 'content': None}, "", "", ""

    if content is not None:
        try:
            # Just store the base64 string in dcc.Store
            return (
                {'filename': filename, 'content': content},
                f'Uploaded "{filename}"',
                "",
                ""
            )
        except Exception as e:
            return (
                {'filename': None, 'content': None},
                f'Upload failed: {str(e)}',
                "",
                ""
            )

    # If no content and no reset clicked, do nothing
    raise dash.exceptions.PreventUpdate


@app.callback(
    Output('converted-image-container', 'children'),
    Output('conversion-message', 'children'),
    Input('convert-button', 'n_clicks'),
    State('upload-store', 'data'),
    State('output-format', 'value')
)
def convert_image(n_clicks, upload_data, output_format):
    """
    Convert the in-memory image to the selected format and show it.
    """
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if not upload_data or not upload_data['content']:
        return "", "Please upload an image first."

    if not output_format:
        return "", "Please select an output format."

    try:
        # Decode the stored image
        content_type, content_string = upload_data['content'].split(',')
        decoded = base64.b64decode(content_string)
        image = Image.open(io.BytesIO(decoded))

        # Convert the image in memory
        converted = io.BytesIO()
        image.save(converted, format=output_format.upper())
        converted.seek(0)

        # Convert to base64 for display
        encoded_image = base64.b64encode(converted.read()).decode('utf-8')
        data_url = f"data:image/{output_format};base64,{encoded_image}"

        return html.Img(src=data_url, style={'max-width': '500px'}), "Image converted successfully!"
    except Exception as e:
        return "", f"Conversion failed: {str(e)}"


if __name__ == "__main__":
    # For Render, take PORT from env (default=8050)
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
