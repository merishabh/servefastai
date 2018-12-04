import base64
import json
import torch

from io import BytesIO
from flask import Flask, render_template, request
from fastai.vision import *
from fastai import *
from PIL import Image as PILImage


app = Flask(__name__)

with open('model_cfg.json') as f:
    model_cfg = json.load(f)

def get_model_from_name(model_name):
    if model_name == 'resnet18':
        return models.resnet18
    if model_name == 'resnet34':
        return models.resnet34
    if model_name == 'resnet50':
        return models.resnet50

path = Path("/tmp")
classes = model_cfg["output_classes"]
data = ImageDataBunch.single_from_classes(path, classes, tfms=get_transforms(), size=model_cfg["image_size"]).normalize(imagenet_stats)
learner = create_cnn(data, get_model_from_name(model_cfg["model_arch"]))
learner.model.load_state_dict(
    torch.load("model.pth", map_location="cpu")
)

@app.route('/')
def upload():
    return render_template('upload.html')

def set_model(self, model):
    self.model = model

def encode(img):
    img = (image2np(img.data) * 255).astype('uint8')
    pil_img = PILImage.fromarray(img)
    pil_img.thumbnail((224,224))
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")
    return base64.b64encode(buff.getvalue()).decode("utf-8")

def _predict_single(fp):
    img = open_image(fp)
    pred_class,pred_idx,outputs = learner.predict(img)
    img_data = encode(img)
    return { 'label': pred_class, 'name': fp.filename, 'image': img_data }

@app.route('/predict', methods=['POST'])
def predict():
    files = request.files.getlist("files")
    predictions = map(_predict_single, files)
    return render_template('predict.html', predictions=predictions)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT",5000))
    app.run(host='0.0.0.0', port=port)