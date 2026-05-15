import io
import os
import cv2
import numpy as np
from PIL import Image
import torch
import torchvision.transforms.functional as F
from flask import Flask, request, send_file, jsonify
from Unet import UNet
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model/last.pt")
SCALE = 0.5
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None


class PILToTensor:
    def __call__(self, image):
        image = F.pil_to_tensor(image)
        return image


class ToDtype:
    def __init__(self, dtype, scale=True):
        self.dtype = dtype
        self.scale = scale

    def __call__(self, image):
        if self.scale:
            image = F.convert_image_dtype(image, self.dtype)
        else:
            image = image.to(dtype=self.dtype)
        return image


class Normalize:
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, image):
        image = F.normalize(image, mean=self.mean, std=self.std)
        return image


class Compose:
    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, image):
        for t in self.transforms:
            image = t(image)
        return image


class InferenceAugmentation:
    def __init__(self, scale) -> None:
        self.scale = scale
        self.transforms = Compose([
            PILToTensor(),
            ToDtype(dtype=torch.float, scale=True),
            Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
        ])

    def __call__(self, image):
        image = self.resize(image)
        return self.transforms(image)

    def resize(self, image):
        w, h = image.size
        newW, newH = int(self.scale * w), int(self.scale * h)
        image = image.resize((newW, newH), Image.BICUBIC)
        return image


def resize(image, scale):
    w, h = image.size
    newW, newH = int(scale * w), int(scale * h)
    image = image.resize((newW, newH), Image.BICUBIC)
    return image


def load_model():
    global model
    if model is None:
        model = UNet(in_channels=3, num_classes=2)
        state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
        for key in state_dict.keys():
            state_dict[key] = state_dict[key].float()
        model.load_state_dict(state_dict, strict=False)
        model.to(DEVICE)
        model.eval()
    return model


def inference(image_bytes):
    model = load_model()
    preprocess = InferenceAugmentation(scale=SCALE)

    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        output = model(input_batch)[0]

    output_predictions = output.argmax(0).cpu().numpy()
    return input_image, output_predictions


color_palette = [
    (0, 0, 0),
    (255, 0, 0),
]


def visualize_segmentation_map(image, segmentation_mask, mode="overlay"):
    image = np.array(image).copy().astype(np.uint8)
    segmentation_mask = segmentation_mask.copy().astype(np.uint8)

    h, w = segmentation_mask.shape

    if mode == "overlay":
        bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        rgba_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2BGRA)
        rgba_image[segmentation_mask == 1, 3] = 0
        return rgba_image, None
    else:
        colored_segmentation = np.zeros((h, w, 3), dtype=np.uint8)
        for class_id, color in enumerate(color_palette):
            colored_segmentation[segmentation_mask == class_id] = color
        result_image = cv2.cvtColor(colored_segmentation, cv2.COLOR_RGB2BGR)
        return result_image, colored_segmentation


@app.route("/segment", methods=["POST"])
def segment():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    image_bytes = file.read()

    try:
        input_image, segmentation_map = inference(image_bytes)
        input_image_resized = resize(input_image, SCALE)
        output_type = request.form.get("type", "overlay")
        if output_type == "mask":
            result_image, _ = visualize_segmentation_map(input_image_resized, segmentation_map, mode="mask")
        elif output_type == "overlay":
            result_image, _ = visualize_segmentation_map(input_image_resized, segmentation_map, mode="overlay")
        else:
            return jsonify({"error": "Invalid type. Use 'mask' or 'overlay'"}), 400

        result_bytes = cv2.imencode(".png", result_image)[1].tobytes()
        return send_file(io.BytesIO(result_bytes), mimetype="image/png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "device": str(DEVICE)})


if __name__ == "__main__":
    load_model()
    app.run(host="0.0.0.0", port=5000, debug=True)
