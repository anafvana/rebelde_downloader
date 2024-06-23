Me, in Tim Curry @ Psych voice: He can't even multithread!

rebelde_downloader: Jes, I can

## For Servers

Manually install `chromedriver` and `chrome`

### `chromedriver`

```
wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
unzip -x chromedriver_linux64.zip
sudo chown root:root chromedriver
sudo chmod +x chromedriver
mv chromedriver /usr/bin/
```

### `chrome`

```
wget https://storage.googleapis.com/chrome-for-testing-public/114.0.5735.90/linux64/chrome-linux64.zip
sudo mv chrome-linux64 /opt/chrome-linux
export PATH=$PATH:/opt/chrome-linux
sudo ln -s /opt/chrome-linux/chrome /usr/bin/google-chrome
```
