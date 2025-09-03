git clone https://github.com/jagrut-thakare/Drishyam_BGR.git
cd Drishyam_BGR
mkdir model
cd Drishyam_BG/model
wget https://github.com/ZhengPeng7/BiRefNet/releases/download/v1/BiRefNet-DIS-epoch_590.pth
conda run -n drishyam --live-stream pip install -r requirements.txt
conda run -n drishyam --live-stream conda install -c conda-forge libstdcxx-ng -y
echo 'export PYTHONPATH="$(pwd)"' >> ~/.bashrc