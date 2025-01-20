import dash
from dash import dcc, html, Input, Output, State, callback_context
import os
import io
import base64
from PIL import Image
from pillow_heif import register_heif_opener
import dash_bootstrap_components as dbc

# Register HEIC support
register_heif_opener()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define initial state variables
state = {
    'uploaded_filename': '',
    'upload_message': '',
    'conversion_message': '',
    'converted_image': None
}

app.layout = dbc.Container([
    html.H1("Image Converter"),
    dbc.Row([
        dbc.Col([
            dbc.FileUpload(
                id='upload-image',
                multiple=False,
                children='Drag and Drop or Browse File'
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
            dbc.Button("Convert and Download", id="convert-button"),
            html.Div(id='conversion-message'),
        ], width=6)
    ]),
    html.Div(id='converted-image-container'),
    dbc.Button("Reset", id="reset-button"),
])

@app.callback(
    Output('upload-data', 'children'),
    Output('upload-message', 'children'),
    Output('converted-image-container', 'children'),
    Output('conversion-message', 'children'),
    Input('upload-image', 'contents'),
    State('upload-image', 'filename'),
    State('upload-image', 'last_modified'),
    Input('reset-button', 'n_clicks')
)
def update_app(content, filename, last_modified, n_clicks):
    # Handle reset button click
    if n_clicks:
        state['uploaded_filename'] = ''
        state['upload_message'] = ''
        state['conversion_message'] = ''
        state['converted_image'] = None
        return dbc.FileUpload(
            id='upload-image',
            multiple=False,
            children='Drag and Drop or Browse File'
        ), '', '', ''

    # Handle image upload
    if content is not None:
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        try:
            with io.BytesIO(decoded) as image_stream:
                image = Image.open(image_stream)
                state['uploaded_filename'] = filename
                state['upload_message'] = f'Uploaded "{filename}"'
                return dbc.FileUpload(
                    id='upload-image',
                    multiple=False,
                    children='Drag and Drop or Browse File'
                ), state['upload_message'], '', ''
        except Exception as e:
            state['upload_message'] = f'Upload failed: {str(e)}'
            return dbc.FileUpload(
                id='upload-image',
                multiple=False,
                children='Drag and Drop or Browse File'
            ), state['upload_message'], '', ''

    # Return initial state
    return dbc.FileUpload(
        id='upload-image',
        multiple=False,
        children='Drag and Drop or Browse File'
    ), '', '', ''

@app.callback(
    Output('converted-image-container', 'children'),
    Output('conversion-message', 'children'),
    Input('convert-button', 'n_clicks'),
    State('upload-image', 'filename'),
    State('output-format', 'value')
)
def convert_image(n_clicks, filename, output_format):
    if n_clicks is None:
        return '', ''

    if filename is None:
        return '', 'Please upload an image first.'

    try:
        # Load the uploaded image
        image = Image.open(f'uploads/{filename}')

        # Convert the image to the selected format
        converted_image = io.BytesIO()
        image.save(converted_image, format=output_format)
        converted_image.seek(0)

        # Create a data URL for the converted image
        encoded_image = base64.b64encode(converted_image.read()).decode('utf-8')
        data_url = f"data:image/{output_format};base64,{encoded_image}"

        # Display the converted image
        return html.Img(src=data_url, style={'max-width': '500px'}), 'Image converted successfully!'

    except Exception as e:
        return '', f'Conversion failed: {str(e)}'

if __name__ == '__main__':
    app.run_server(debug=False)
