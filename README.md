# distance #
A python script to run as service on a raspberry pi with an VL53L1X sensor attached to I2C bus;
The script messures the distance and calls an http endpoint if the distance is between a minimum and maximum value;

## Installation ##
pip3 install VL53L1X
sudo cp distance.service /etc/systemd/system
sudo systemctl enable distance.service
sudo systemctl start distance.service

