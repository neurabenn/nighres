# Generated by: Neurodocker version 0.7.0+0.gdc97516.dirty
# Latest release: Neurodocker version 0.8.0
# Timestamp: 2022/03/30 14:33:11 UTC
# 
# Thank you for using Neurodocker. If you discover any issues
# or ways to improve this software, please submit an issue or
# pull request on our GitHub repository:
# 
#     https://github.com/ReproNim/neurodocker

FROM debian:stretch-slim

USER root

ARG DEBIAN_FRONTEND="noninteractive"

ENV LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8" \
    ND_ENTRYPOINT="/neurodocker/startup.sh"
RUN export ND_ENTRYPOINT="/neurodocker/startup.sh" \
    && apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           apt-utils \
           bzip2 \
           ca-certificates \
           curl \
           locales \
           unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG="en_US.UTF-8" \
    && chmod 777 /opt && chmod a+s /opt \
    && mkdir -p /neurodocker \
    && if [ ! -f "$ND_ENTRYPOINT" ]; then \
         echo '#!/usr/bin/env bash' >> "$ND_ENTRYPOINT" \
    &&   echo 'set -e' >> "$ND_ENTRYPOINT" \
    &&   echo 'export USER="${USER:=`whoami`}"' >> "$ND_ENTRYPOINT" \
    &&   echo 'if [ -n "$1" ]; then "$@"; else /usr/bin/env bash; fi' >> "$ND_ENTRYPOINT"; \
    fi \
    && chmod -R 777 /neurodocker && chmod a+s /neurodocker

ENTRYPOINT ["/neurodocker/startup.sh"]

RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           openjdk-8-jdk git wget build-essential software-properties-common libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV CONDA_DIR="/opt/miniconda-latest" \
    PATH="/opt/miniconda-latest/bin:$PATH"
RUN export PATH="/opt/miniconda-latest/bin:$PATH" \
    && echo "Downloading Miniconda installer ..." \
    && conda_installer="/tmp/miniconda.sh" \
    && curl -fsSL --retry 5 -o "$conda_installer" https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash "$conda_installer" -b -p /opt/miniconda-latest \
    && rm -f "$conda_installer" \
    && conda update -yq -nbase conda \
    && conda config --system --prepend channels conda-forge \
    && conda config --system --set auto_update_conda false \
    && conda config --system --set show_channel_urls true \
    && sync && conda clean -y --all && sync \
    && conda create -y -q --name nighres \
    && conda install -y -q --name nighres \
           "python=3.9" \
           "pip" \
           "jcc" \
           "gcc_linux-64" \
           "gxx_linux-64" \
           "Nilearn" \
    && sync && conda clean -y --all && sync \
    && sed -i '$isource activate nighres' $ND_ENTRYPOINT

ENV JAVA_HOME="/docker-java-home"

ENV JCC_JDK="/docker-java-home"

RUN ln -svT "/usr/lib/jvm/java-8-openjdk-$(dpkg --print-architecture)" /docker-java-home

COPY ["build.sh", "cbstools-lib-files.sh", "setup.py", "MANIFEST.in", "README.rst", "LICENSE", "imcntk-lib-files.sh", "/home/neuro/nighres/"]

COPY ["nighres", "/home/neuro/nighres/nighres"]

WORKDIR /home/neuro/nighres

RUN conda init && . /root/.bashrc && conda activate nighres && conda info --envs && ./build.sh && rm -rf cbstools-public imcn-imaging nighresjava/build nighresjava/src

RUN conda install -y -q --name nighres \
           "jupyter" \
    && sync && conda clean -y --all && sync \
    && bash -c "source activate nighres \
    &&   pip install --no-cache-dir  \
             "."" \
    && rm -rf ~/.cache/pip/* \
    && sync

COPY ["docker/jupyter_notebook_config.py", "/etc/jupyter"]

EXPOSE 8888

RUN chmod -R 777 /home/neuro/

RUN test "$(getent passwd neuro)" || useradd --no-user-group --create-home --shell /bin/bash neuro
USER neuro

CMD ["jupyter notebook --no-browser --ip 0.0.0.0"]

RUN echo '{ \
    \n  "pkg_manager": "apt", \
    \n  "instructions": [ \
    \n    [ \
    \n      "base", \
    \n      "debian:stretch-slim" \
    \n    ], \
    \n    [ \
    \n      "install", \
    \n      [ \
    \n        "openjdk-8-jdk git wget build-essential software-properties-common libffi-dev" \
    \n      ] \
    \n    ], \
    \n    [ \
    \n      "miniconda", \
    \n      { \
    \n        "create_env": "nighres", \
    \n        "conda_install": [ \
    \n          "python=3.9", \
    \n          "pip", \
    \n          "jcc", \
    \n          "gcc_linux-64", \
    \n          "gxx_linux-64", \
    \n          "Nilearn" \
    \n        ], \
    \n        "activate": true \
    \n      } \
    \n    ], \
    \n    [ \
    \n      "env", \
    \n      { \
    \n        "JAVA_HOME": "/docker-java-home" \
    \n      } \
    \n    ], \
    \n    [ \
    \n      "env", \
    \n      { \
    \n        "JCC_JDK": "/docker-java-home" \
    \n      } \
    \n    ], \
    \n    [ \
    \n      "run", \
    \n      "ln -svT \"/usr/lib/jvm/java-8-openjdk-$(dpkg --print-architecture)\" /docker-java-home" \
    \n    ], \
    \n    [ \
    \n      "copy", \
    \n      [ \
    \n        "build.sh", \
    \n        "cbstools-lib-files.sh", \
    \n        "setup.py", \
    \n        "MANIFEST.in", \
    \n        "README.rst", \
    \n        "LICENSE", \
    \n        "imcntk-lib-files.sh", \
    \n        "/home/neuro/nighres/" \
    \n      ] \
    \n    ], \
    \n    [ \
    \n      "copy", \
    \n      [ \
    \n        "nighres", \
    \n        "/home/neuro/nighres/nighres" \
    \n      ] \
    \n    ], \
    \n    [ \
    \n      "workdir", \
    \n      "/home/neuro/nighres" \
    \n    ], \
    \n    [ \
    \n      "run", \
    \n      "conda init && . /root/.bashrc && conda activate nighres && conda info --envs && ./build.sh && rm -rf cbstools-public imcn-imaging nighresjava/build nighresjava/src" \
    \n    ], \
    \n    [ \
    \n      "miniconda", \
    \n      { \
    \n        "use_env": "nighres", \
    \n        "conda_install": [ \
    \n          "jupyter" \
    \n        ], \
    \n        "pip_install": [ \
    \n          "." \
    \n        ] \
    \n      } \
    \n    ], \
    \n    [ \
    \n      "copy", \
    \n      [ \
    \n        "docker/jupyter_notebook_config.py", \
    \n        "/etc/jupyter" \
    \n      ] \
    \n    ], \
    \n    [ \
    \n      "expose", \
    \n      [ \
    \n        "8888" \
    \n      ] \
    \n    ], \
    \n    [ \
    \n      "run", \
    \n      "chmod -R 777 /home/neuro/" \
    \n    ], \
    \n    [ \
    \n      "user", \
    \n      "neuro" \
    \n    ], \
    \n    [ \
    \n      "cmd", \
    \n      [ \
    \n        "jupyter notebook --no-browser --ip 0.0.0.0" \
    \n      ] \
    \n    ] \
    \n  ] \
    \n}' > /neurodocker/neurodocker_specs.json
