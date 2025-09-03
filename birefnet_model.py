import torch
from PIL import Image, ImageOps, ImageFilter
from torchvision import transforms
from models.birefnet import BiRefNet
import cv2
from config import Config
import numpy as np

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = torch.device("cpu")

config = Config()
model = BiRefNet(bb_pretrained=False)
model.load_state_dict(torch.load("model/BiRefNet-DIS-epoch_590.pth", map_location=device))
model.to(device)
model.eval()

input_size = (352, 352)  # Expected input size of the model

def generate_mask(input_path, output_path):
    # --- Load and preprocess image ---
    image = Image.open(input_path).convert("RGB")
    original_size = image.size

    transform = transforms.Compose([
        transforms.Resize(input_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                            [0.229, 0.224, 0.225])
    ])
    input_tensor = transform(image).unsqueeze(0).to(device)

        # --- Inference ---
    with torch.no_grad():
        output = model(input_tensor)

    # --- Post-processing ---
    # Access the first element of the output list before applying sigmoid
    output = torch.sigmoid(output[0])
    output = transforms.ToPILImage()(output.squeeze(0).cpu())

    # Resize saliency map back to original image size
    output = output.resize(original_size, resample=Image.BILINEAR)
    output = ImageOps.invert(output)

    # Optional: binarize the inverted mask if you want sharp edges
    threshold = 128
    output = output.convert("L").point(lambda p: 255 if p > threshold else 0)
    output = output.filter(ImageFilter.GaussianBlur(radius=4))


    output.save(output_path)
    print(f"Background mask (for inpainting) saved to {output_path}")