#
FROM muccg/python-base:ubuntu14.04-2.7
MAINTAINER https://bitbucket.org/ccgmurdoch/rdrf/

ENV DEBIAN_FRONTEND noninteractive

# Project specific deps
RUN apt-get update && apt-get install -y --no-install-recommends \
  libpcre3 \
  libpcre3-dev \
  libpq-dev \
  libssl-dev \
  libyaml-dev \
  python-tk \
  sendmail \
  git \
  zlib1g-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN env --unset=DEBIAN_FRONTEND

# Deps for tests
RUN pip install \
  lettuce \
  lettuce_webdriver \
  pyvirtualdisplay \
  nose \
  selenium

# Install dependencies only (not the app itself) to use the build cache more efficiently
# This will be redone only if setup.py changes
# INSTALL_ONLY_DEPENDENCIES stops the app installing inside setup.py (pip --deps-only ??)
COPY rdrf/setup.py /app/rdrf/setup.py
WORKDIR /app/rdrf
RUN INSTALL_ONLY_DEPENDENCIES=True pip install --trusted-host github.com --allow-all-external --process-dependency-links .

# Copy code and install the app
COPY . /app
RUN pip install --process-dependency-links --no-deps -e .

# now that we have installed everything globally purge /app
# /app gets added as a volume at run time
WORKDIR /app
RUN rm -rf ..?* .[!.]* *

EXPOSE 8000 9000 9001 9100 9101
VOLUME ["/app", "/data"]

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV HOME /data
WORKDIR /data

# entrypoint shell script that by default starts runserver
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["runserver"]
