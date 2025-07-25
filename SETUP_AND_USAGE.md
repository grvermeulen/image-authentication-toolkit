# Image Authentication Toolkit: Setup, Usage, and Testing Guide

## 1. Prerequisites
- **Python 3.x** (use `python3` and `pip3`)
- **Docker** and **Docker Compose**
- (Optional) Git for version control

## 2. Initial Setup
```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd image-authentication-toolkit

# Install Python dependencies (if running outside Docker)
pip3 install --upgrade pip
pip3 install flask requests pillow numpy
```

## 3. Keeping Dependencies Up to Date
After every `git pull`, run:
```bash
pip3 install --upgrade -r requirements.txt  # In each subproject with requirements.txt
docker compose build --pull
docker compose up -d
```

## 4. Running the App Locally
```bash
docker compose up -d
docker compose ps  # Check that all containers are 'Up'
```
- Open [http://localhost:8080](http://localhost:8080) in your browser to access the UI.

## 5. Running Tests
Make sure the containers are running, then run:
```bash
python3 test_upload.py
```
- This script simulates an image upload and prints the result.

## 6. Best Practices
- **After code or dependency changes:**
  ```bash
  docker compose build --pull && docker compose up -d
  ```
- **Wait a few seconds after starting containers** before running tests.
- **Check container status:**
  ```bash
  docker compose ps
  ```
- **Check logs for errors:**
  ```bash
  docker compose logs flask-ui
  docker compose logs foto-forensics
  ```
- **Manual UI test:** Open [http://localhost:8080](http://localhost:8080)
- **To reset everything:**
  ```bash
  docker compose down -v
  ```

## 7. Troubleshooting
- If you see `Connection refused` errors, make sure containers are running and healthy.
- If you see `ModuleNotFoundError` (e.g., for Pillow), rebuild the container:
  ```bash
  docker compose build flask-ui && docker compose up -d flask-ui
  ```
- If Docker install fails due to `containerd` conflicts:
  ```bash
  sudo apt-get remove -y containerd
  sudo apt-get update
  curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
  sudo apt-get install -y docker-compose-plugin
  ```

## 8. Additional Notes
- Use `python3` and `pip3` for all commands.
- For best ELA results, use both original and manipulated images for comparison.
- If you add more tests, update the test command and document new procedures.
- If you need to automate these steps, consider writing a shell script.

---

For more help, check the project README or contact the maintainer. 