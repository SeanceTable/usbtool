# Remote iOS Testing Station

A powerful solution for remote iOS app testing that combines USB over network capabilities with web-based screen sharing. Allow testers to connect their iOS devices remotely and interact with your testing application through any web browser.

![Remote iOS Testing](https://img.shields.io/badge/Platform-macOS-blue)
![Python Version](https://img.shields.io/badge/Python-3.7+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![VirtualHere](https://img.shields.io/badge/USB-VirtualHere-orange)

## 🌟 Features

### 🌐 Web-Based Remote Access
- **Live screen streaming** of your Mac testing application
- **Real-time click/touch forwarding** from browser to your app
- **Keyboard input support** for remote interaction
- **Responsive web interface** that works on any device

### 📱 USB Over Network
- **Automatic VirtualHere installation** and configuration
- **Remote USB device detection** and management
- **Session-based testing** with automatic timeouts
- **Device queue management** for multiple testers

### 🖥️ Smart Display Management
- **Kiosk mode** - testers only see your testing app
- **Automatic window detection** and capture
- **Click coordinate translation** for accurate interaction
- **Fullscreen support** for immersive testing

### ⚡ Automated Workflow
- **One-command setup** - everything configured automatically
- **Cross-platform support** (macOS, Linux, Windows)
- **Real-time status monitoring** for USB and app connections
- **Error handling and recovery** for reliable operation

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip3 install pyautogui pillow

# Ensure your Mac has:
# - macOS 10.14+ (for screen capture permissions)
# - Your iOS testing application
# - Network access for remote connections
```

### Installation & Usage

1. **Download the script**
```bash
git clone https://github.com/SeanceTable/usbtool.git
cd remote-ios-testing-station
```

2. **Run the testing station**
```bash
python3 testing_station.py --program "/Applications/YourTestingApp.app" --web-port 8080
```

3. **Share the URL with testers**
```
http://your-mac-ip:8080
```

4. **Testers connect their devices**
- Remote testers plug iPhone into VirtualHere server at their location
- Access your testing app through their web browser
- Click the upload button to install your app

## 📋 Command Line Options

```bash
# Basic usage
python3 testing_station.py --program "/Applications/YourApp.app"

# Custom web port
python3 testing_station.py --program "/Applications/YourApp.app" --web-port 9000

# Connect to remote VirtualHere server
python3 testing_station.py --program "/Applications/YourApp.app" --server "192.168.1.100"

# Skip automatic VirtualHere installation
python3 testing_station.py --program "/Applications/YourApp.app" --no-auto-install

# Install VirtualHere only
python3 testing_station.py --action install-only
```

## 🌍 Network Setup

### Port Forwarding Requirements

For remote access, configure your router to forward these ports:

```bash
# Required ports:
Port 8080 → Your Mac:8080  # Web interface (customizable)
Port 7572 → Your Mac:7572  # VirtualHere USB server (if hosting)
Port 7575 → Your Mac:7575  # VirtualHere client API
```

### VirtualHere Server Setup

Remote locations need VirtualHere Server for USB sharing:

```bash
# Download and run VirtualHere server at remote location
wget https://www.virtualhere.com/sites/default/files/usbserver/vhusbdarm64
chmod +x vhusbdarm64
./vhusbdarm64
```

## 🔧 Configuration

### macOS Permissions

Grant necessary permissions when prompted:
- **Screen Recording** (System Preferences > Security & Privacy > Privacy > Screen Recording)
- **Accessibility** (System Preferences > Security & Privacy > Privacy > Accessibility)

### Firewall Configuration

```bash
# Allow the script through macOS firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add ~/VirtualHere/vhclientx64
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock ~/VirtualHere/vhclientx64
```

## 📱 Tester Workflow

1. **Access Testing Interface**
   - Open `http://your-mac-ip:8080` in any web browser
   - See live view of your testing application

2. **Connect iOS Device**
   - Plug iPhone/iPad into local VirtualHere server
   - Device appears automatically in the web interface

3. **Test Your App**
   - See "Phone Connected" status in browser
   - Click "Install App" button through web interface
   - App installs on their device via USB over internet

4. **Session Management**
   - Each session lasts 60 seconds
   - Automatic queue management for multiple testers
   - Real-time status updates

## 🏗️ Architecture

```
Remote Tester Location:           Your Mac:
┌─────────────────────┐          ┌─────────────────────┐
│ iPhone → USB Server │ ────────▶│ VirtualHere Client  │
│ Browser ────────────│ ────────▶│ Web Server          │
└─────────────────────┘          │ Testing Application │
                                 └─────────────────────┘
```

## 🛠️ Troubleshooting

### Common Issues

**VirtualHere Connection Failed**
```bash
# Check if VirtualHere client is running
ps aux | grep vhclient

# Restart VirtualHere client
python3 testing_station.py --action install-only
```

**Web Interface Not Loading**
```bash
# Check if port is available
lsof -i :8080

# Try different port
python3 testing_station.py --program "/Applications/YourApp.app" --web-port 9000
```

**Screen Capture Not Working**
- Go to System Preferences > Security & Privacy > Privacy > Screen Recording
- Add Terminal or your Python installation to allowed apps

### Performance Optimization

- Use wired internet connection for best performance
- Close unnecessary applications to improve screen capture speed
- Consider using a dedicated testing Mac for optimal performance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

**Created by SeanceTable**

This project leverages several excellent open-source technologies:
- [VirtualHere](https://www.virtualhere.com/) - USB over network technology
- [PyAutoGUI](https://github.com/asweigart/pyautogui) - Cross-platform GUI automation
- [Pillow](https://github.com/python-pillow/Pillow) - Python Imaging Library

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/remote-ios-testing-station/issues) page
2. Create a new issue with detailed description
3. Include your system information and error logs

## 🎯 Use Cases

- **Remote iOS app testing** for distributed teams
- **Beta testing** with users worldwide
- **QA testing** without physical device access
- **Demo presentations** to remote clients
- **Educational environments** for iOS development courses

## 🔮 Future Enhancements

- [ ] Multi-device simultaneous testing
- [ ] Recording and playback of testing sessions
- [ ] Integration with CI/CD pipelines
- [ ] Advanced device filtering and selection
- [ ] Built-in screen recording capabilities
- [ ] WebRTC for lower latency streaming

---

**Made with ❤️ by SeanceTable**

⭐ Star this repository if you find it useful!
