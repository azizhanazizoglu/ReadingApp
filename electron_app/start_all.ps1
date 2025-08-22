# PowerShell script to build React app and start Electron

# Go to React UI folder and build
Write-Host "Building React UI..."
cd ../react_ui
npm run build

# Go to Electron app folder and install dependencies
Write-Host "Installing Electron dependencies..."
cd ../electron_app
npm install

# Start Electron app
Write-Host "Starting Electron app..."
npm start
