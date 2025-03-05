<div align="center">
<br/>
<h1>NeuroDUI</h1>
<h3>Neuro Data User Interface</h3>
<br/>
<img src="https://img.shields.io/badge/Python-14354C?style=for-the-badge&logo=python&logoColor=white" alt="built with Python3" />
<img src="https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white" alt="built with SQLite" />
<img src="https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white" alt="built with HTML" />
<img src="https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white" alt="built with CSS" />
<img src="https://img.shields.io/badge/shell_script-%23121011.svg?style=for-the-badge&logo=gnu-bash&logoColor=white" alt="built with Shell Script" />


</div>





## Installation

### Source code
First clone the repository, then run `pip3 install -r requirements.txt` inside of the repository folder.

### PyPI
\<to be added\>

### Linux dependencies
This app is designed for linux distributions. You can install the dependecises for linux using the following command:
```console
Amin@Maximus:./Data-Manager$ bash requirements_linux.sh

```

## Usage
Please take a look at [here](https://github.com/AminAlam/Data-Manager/wiki) for documentations.

After installing the dependencies, you can run the program via following command:
```console
Amin@Maximus:./Data-Manager$ python3 src/main.py --server_ip localhost --port 8080

```
You can access the app via the following url http://localhost:8080. It is also possible to run the program on a different PORT (Please make sure that PORT is open in your firewall settings). 
The default username and password are *admin* and *admin* (You can change this password in the <em>profile</em> tab).

## Documentation

Please take a look at [here](https://github.com/AminAlam/Data-Manager/wiki) for the full documentation.

# LLM-Powered Search Assistant

This application includes a natural language search assistant powered by Llama.

## Model Setup Instructions

1. Create a `models` directory in the root of your project:
   ```
   mkdir -p models
   ```

2. Download a GGUF format Llama model. You can get models from Hugging Face:
   - For a smaller model: [Llama-2-7B-Chat-GGUF](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)
   - For better quality: [Llama-2-13B-Chat-GGUF](https://huggingface.co/TheBloke/Llama-2-13B-Chat-GGUF)

3. Download the appropriate quantized version based on your hardware capabilities:
   - For limited RAM: Use the Q4_K_M or Q4_0 versions
   - For more RAM: Use Q5_K_M or Q8_0 for better quality

4. Place the downloaded model in the `models` directory and update the model path in `src/web/api.py`:
   ```python
   self.llm_search = LlamaSearch(
       model_path="models/your-model-filename.gguf",
       n_threads=num_threads
   )
   ```

5. Restart your application and the search assistant will be ready to use!

## Environment Variables

The application now uses environment variables for configuration instead of the previous `creds.json` file. To set up your environment:

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and fill in your configuration values:
   ```
   # Data Manager Environment Variables
   
   # Flask Secret Key
   SECRET_KEY=your_secret_key_here
   
   # reCAPTCHA Keys
   RECAPTCHA_PUBLIC_KEY=your_recaptcha_public_key
   RECAPTCHA_PRIVATE_KEY=your_recaptcha_private_key
   
   # Email Configuration
   SENDER_EMAIL_ADDRESS=your_email@example.com
   SENDER_EMAIL_PASSWORD=your_email_password
   
   # Claude API Key
   CLAUDE_API_KEY=your_claude_api_key
   ```

3. Make sure to install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. The application will automatically load these environment variables at startup.

**Note:** Never commit your `.env` file to version control. It's already added to `.gitignore`.
