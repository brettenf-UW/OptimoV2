const { spawn } = require('child_process');
const path = require('path');

console.log('Starting OptimoV2 Frontend Development Environment...\n');

// Start mock server
console.log('Starting Mock API Server on port 5000...');
const mockServer = spawn('node', ['mock-server.js'], {
  stdio: 'inherit',
  shell: true
});

// Wait a bit then start React
setTimeout(() => {
  console.log('\nStarting React App on port 3000...');
  console.log('Browser will open automatically in ~30 seconds\n');
  
  const reactApp = spawn('npm', ['start'], {
    stdio: 'inherit',
    shell: true
  });
  
  // Handle exit
  process.on('SIGINT', () => {
    console.log('\nShutting down...');
    mockServer.kill();
    reactApp.kill();
    process.exit();
  });
}, 2000);