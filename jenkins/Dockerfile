FROM jenkins/jenkins:lts-jdk21

USER root

# Base tools needed to download and extract PowerShell
RUN apt-get update && apt-get install -y \
        curl \
        tar \
        libicu-dev \
        iputils-ping \
        python3 \
        python3-pip \
        python3-venv \
        openssh-client \
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

# --- Ansible (control node only) ---
# Installed into an isolated venv rather than system pip, since Debian-based images
# enforce PEP 668 (externally-managed-environment) and block plain system-wide pip installs.
RUN python3 -m venv /opt/ansible-venv \
    && /opt/ansible-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/ansible-venv/bin/pip install --no-cache-dir \
        "ansible-core==2.17.*"

# Make ansible / ansible-playbook / ansible-vault available on PATH
ENV PATH="/opt/ansible-venv/bin:${PATH}"

# --- Ansible Windows collections ---
# These provide the Windows-targeted modules (win_service, win_copy, win_template,
# win_unzip, etc.) — written in PowerShell, executed on the Windows host itself.
# Needed regardless of whether the transport is SSH or WinRM.
RUN mkdir -p /usr/share/ansible/collections \
    && ansible-galaxy collection install \
        ansible.windows \
        community.windows \
        -p /usr/share/ansible/collections

ENV ANSIBLE_COLLECTIONS_PATH="/usr/share/ansible/collections"

USER jenkins

# Fail the image build early (not at pipeline runtime) if the install is broken
RUN ansible --version \
    && ansible-galaxy collection list | grep -E "ansible\.windows|community\.windows"