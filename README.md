# Early-Signal-Detection-in-the-Luxury-Handbag-Market

# 1. Create a fresh virtual environment
python -m venv .venv

# 2. Activate it
source .venv/bin/activate        # Mac/Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Register it as a Jupyter kernel
pip install ipykernel
python -m ipykernel install --user --name=.venv

# 5. Open the notebook and select the .venv kernel
jupyter notebook Main.ipynb

# 6. For context, read this:
Run only Main.ipynb -- 
The .py files are uploaded as proof to how the data was collected, however it is not necessary to run them for the pipeline to work. 
