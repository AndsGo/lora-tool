@REM Installs the project dependencies.
@REM Install dependencies.
pip install torch==2.7.0+cu128 torchvision==0.22.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128
pip install -U -I --no-deps xformers==0.0.30 --extra-index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
@REM 安装spacy
python -m spacy download en_core_web_lg
