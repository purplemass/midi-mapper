sudo apt update
sudo apt upgrade -y
sudo apt install libjack-dev libasound2-dev -y
sudo apt install python3-pip -y
sudo apt autoremove -y
sudo apt-get clean
pip3 install -r requirements-pi.txt
sudo reboot
