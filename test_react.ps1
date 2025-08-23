# Windows PowerShell script to build React UI and start Electron app from root
cd react_ui
npm install
npm run build
cd ..
cd electron_app
./start_all.ps1
