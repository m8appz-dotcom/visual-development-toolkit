FROM node:24-bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates git ffmpeg gcc g++ make libicu72 libssl3 zlib1g libgomp1 curl && rm -rf /var/lib/apt/lists/*
COPY downloads/dotnet /usr/share/dotnet
COPY downloads/jdk21/runtime /opt/java
RUN ln -s /usr/share/dotnet/dotnet /usr/local/bin/dotnet
COPY downloads/ghidra/ghidra_12.1.4_PUBLIC /opt/ghidra
ENV JAVA_HOME=/opt/java GHIDRA_INSTALL_DIR=/opt/ghidra REA_ANALYSIS_PROVIDER=ghidra
ENV PATH=/opt/java/bin:$PATH
COPY requirements/docker-constraints.txt /opt/python-constraints.txt
COPY sources/ghidra-headless-mcp /opt/ghidra-mcp
COPY sources/universal-modder /opt/universal-modder
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -c /opt/python-constraints.txt /opt/ghidra-mcp /opt/universal-modder UnityPy mcp
ENV PATH=/opt/venv/bin:/opt/dotnet-tools:/usr/local/bin:$PATH
COPY downloads/ilspy-tools /opt/ilspy-tools
RUN npm install -g rea-agents@4.1.0 && printf '#!/bin/sh\nexec dotnet /opt/ilspy-tools/.store/ilspycmd/11.1.0.9782/ilspycmd/11.1.0.9782/tools/net10.0/any/ilspycmd.dll "$@"\n' > /usr/local/bin/ilspycmd && chmod +x /usr/local/bin/ilspycmd
RUN useradd -m -u 10001 modder && mkdir -p /lab/projects && chown -R modder:modder /lab
USER modder
WORKDIR /lab/projects
CMD ["sleep", "infinity"]
