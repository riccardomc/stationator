# stationator
Display a page with trains specifically tailored to me.

<img width="846" alt="image" src="https://github.com/user-attachments/assets/41b03f34-7cbf-45c3-9609-533f48205a2a">

## Wait, what?

Yeah, I started commuting again, and I have 4 stations to chose from. Two arrivals and two destinations. In both directions. So, I wrote this thing to get me all the direct trains among those stations so I don't have to query each station combination one by one!

I am simply using the ns.nl API which is quite ok.

## How do you run this thing?

It is run on a small low power computer sitting under my desk at an address I won't disclose. I do something very crude like this:

```
docker pull ghcr.io/riccardomc/stationator:main
docker run -d --name=stationator -e NS_API_KEY=$NS_API_KEY -p8080:8080 ghcr.io/riccardomc/stationator:main
```

To make it restart at boot I create a `/etc/systemd/system/stationator.service` like: 

```
[Unit]
Description=Stationator gives the trains your need
Requires=docker.service
After=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker start -a ghcr.io/riccardomc/stationator:main
ExecStop=/usr/bin/docker stop -t 2 ghcr.io/riccardomc/stationator:main

[Install]
WantedBy=default.target
```

and then enable the service 🤷‍♂️

```
systemctl enable stationator.service
```

## Ok...

This README is mostly for myself, when, 6 months from now I will not remember anything of what I've done when I was sick and bored and built this thing. ❤️
