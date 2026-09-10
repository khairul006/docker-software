FROM jenkins/jenkins:lts-jdk21

USER root

# Base tools needed to download and extract PowerShell
RUN apt-get update && apt-get install -y \
        curl \
        tar \
        libicu-dev \
        iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install PowerShell Core via tarball (avoids Microsoft's .deb repo,
# which targets Ubuntu and can mismatch Debian-based Jenkins images)
RUN mkdir -p /opt/microsoft/powershell/7 \
    && curl -L -o /tmp/powershell.tar.gz \
        https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/powershell-7.4.6-linux-x64.tar.gz \
    && tar -xzf /tmp/powershell.tar.gz -C /opt/microsoft/powershell/7 \
    && chmod +x /opt/microsoft/powershell/7/pwsh \
    && ln -sf /opt/microsoft/powershell/7/pwsh /usr/bin/pwsh \
    && rm /tmp/powershell.tar.gz

USER jenkins