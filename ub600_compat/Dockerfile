# Use the same runtime image as the hardware-tested local app. This is large,
# but supplies Python and kmod without downloading an untested toolchain.
FROM ghcr.io/home-assistant/qemux86-64-homeassistant:2026.9.1
LABEL io.hass.version="0.1.1" io.hass.type="app" io.hass.arch="amd64"
COPY patch_btusb.py compatibility.py run.py /opt/ub600/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/ub600
ENTRYPOINT ["/usr/local/bin/python3", "/opt/ub600/run.py"]
CMD []
