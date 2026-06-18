$port = if ($env:FLASK_RUN_PORT) { $env:FLASK_RUN_PORT } else { "5000" }
$url = if ($env:DEV_OPEN_URL) {
    $env:DEV_OPEN_URL
} else {
    "http://127.0.0.1:$port/api/v1/health/live"
}

Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoProfile",
    "-Command",
    "Start-Sleep -Seconds 2; Start-Process '$url'"
)

python app.py
