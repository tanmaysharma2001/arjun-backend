# summarization-service

## Usage
Clone the application. Make sure to have `python==^3.11` and `poetry` installed.

```bash
poetry install
poetry run uvicorn main:app --host=0.0.0.0
```

## How to deploy

- Create a server (You can create an `ec2` instance using the terraform configuration inside the `infra` folder.)

- Login to the server and install pyenv and nginx. Run the following commands and re-login to see the changes.

```bash
sudo apt update -y
sudo apt install -y nginx python3-pip make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev openssl
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n eval "$(pyenv init -)"\nfi' >> ~/.bashrc
```

- Activate `python3.11` and install `poetry`

```
pyenv install 3.11
pyenv global 3.11
pip install poetry
```

- Clone the repository or remotely copypaste the data. For git, make sure to have authenticated already for this.

```
git clone git@github.com:tanmaysharma2001/arjun-backend.git
cd arjun-backend
```

- Inside the `arjun-backend` folder, create a `.env` file with all api keys. Use `example.env` for reference
- Setup nginx conf. For this, 
  - modify the `infra/arjun.conf` and in line 7, put your own working domain/subdomain instead of `tf.pptx704.com`. 
  - Put this inside `/etc/nginx/sites-enabled` folder
  - Restart nginx using `sudo systemctl restart nginx`. 
  - You should already have a domain/subdomain that points to your server's IP. HTTPS must be enabled. I recommend using cloudflare for easy management.
- Install and run the app

```
poetry install
poetry run uvicorn main:app --host=0.0.0.0
```
- Go to `<your domain>/docs` to see if installation is successful.
- If everything is successful, you can run `poetry run uvicorn main:app --host=0.0.0.0` inside a daemon. To do it with `screen`-
  - Create a screen using `screen -S main`. It will take you to a new screen
  - Run the app using `poetry run uvicorn main:app --host=0.0.0.0`
  - Press `ctrl+A+D` to detach the screen
  - To go back you can run `screen -r main`
  