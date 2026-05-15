import os
import torch
import torchvision.transforms as T
from PIL import Image
from io import BytesIO
from flask import Flask, request, send_file, jsonify
from networks import Generator

app = Flask(__name__)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
CHECKPOINT_PATH = 'model/states_pt_celebahq.pth'

model = None


def load_model():
    global model
    if model is None:
        model = Generator(in_channels=4, out_channels=3, base_channels=64).to(DEVICE)
        if os.path.exists(CHECKPOINT_PATH):
            try:
                state_dict = torch.load(CHECKPOINT_PATH, map_location=DEVICE)
                model.load_state_dict(state_dict)
                print(f"Successfully loaded checkpoint from {CHECKPOINT_PATH}")
            except Exception as e:
                print(f"Warning: Could not load checkpoint: {e}")
                print("Using randomly initialized model.")
        else:
            print(f"Warning: Checkpoint {CHECKPOINT_PATH} not found. Using random weights.")
        model.eval()
    return model


def load_image_from_bytes(img_bytes):
    img = Image.open(BytesIO(img_bytes)).convert('RGB')
    return img


def preprocess_image(img, target_size=256):
    transform = T.Compose([
        T.Resize((target_size, target_size)),
        T.ToTensor(),
    ])
    return transform(img)


def postprocess_image(tensor):
    tensor = tensor.squeeze(0).cpu().detach()
    tensor = torch.clamp(tensor, 0, 1)
    img = T.ToPILImage()(tensor)
    return img


@app.route('/inpaint', methods=['POST'])
def inpaint():
    if 'image' not in request.files or 'mask' not in request.files:
        return jsonify({'error': 'Please provide both image and mask files'}), 400

    image_file = request.files['image']
    mask_file = request.files['mask']
    target_size = request.form.get('size', 256, type=int)

    try:
        image = load_image_from_bytes(image_file.read())
        mask = load_image_from_bytes(mask_file.read())
    except Exception as e:
        return jsonify({'error': f'Failed to load images: {str(e)}'}), 400

    original_size = image.size

    try:
        model = load_model()
        image_tensor = preprocess_image(image, target_size).unsqueeze(0).to(DEVICE)
        mask_tensor = preprocess_image(mask, target_size).unsqueeze(0).to(DEVICE)
        mask_binary = (mask_tensor > 0.5).float()

        with torch.no_grad():
            input_tensor = torch.cat([image_tensor, mask_binary], dim=1)
            output_tensor = model(input_tensor, mask_binary)
            output_tensor = output_tensor * mask_binary + image_tensor * (1 - mask_binary)

        output_image = postprocess_image(output_tensor)
        output_image = output_image.resize(original_size, Image.LANCZOS)

        img_io = BytesIO()
        output_image.save(img_io, format='PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        return jsonify({'error': f'Inference failed: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'device': str(DEVICE)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
