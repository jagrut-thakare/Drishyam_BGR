git clone https://github.com/jagrut-thakare/Drishyam_BGR.git
cd Drishyam_BGR
mkdir model
cd Drishyam_BG/model
wget https://github.com/ZhengPeng7/BiRefNet/releases/download/v1/BiRefNet-DIS-epoch_590.pth
conda run -n birefnet --live-stream pip install -r requirements.txt
conda run -n birefnet --live-stream conda install -c conda-forge libstdcxx-ng -y
echo 'export PYTHONPATH="$(pwd)"' >> ~/.bashrc
echo 'export NO_ALBUMENTATIONS_UPDATE="1"' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$HOME/anaconda3/envs/pratibimb/lib/python3.11/site-packages/nvidia/nvjitlink/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export PYTHONWARNINGS="ignore:resource_tracker:UserWarning"' >> ~/.bashrc
source ~/.bashrc